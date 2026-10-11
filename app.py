
import streamlit as st

from src.verifier import (
    create_evidence_record,
    verify_claim_against_sources,
    create_verification_report,
    export_report_json,
)
from src.pdf_extractor import extract_text_from_pdf
from src.semantic_matcher import calculate_similarity


# --------------------------------------------------
# Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="ProofLoop AI",
    page_icon="🔎",
    layout="wide",
)

SEMANTIC_REVIEW_THRESHOLD = 0.70


# --------------------------------------------------
# Application introduction
# --------------------------------------------------

st.title("🔎 ProofLoop AI")
st.subheader("Evidence-based claim verification")

st.write(
    "Enter a claim and provide evidence from different sources. "
    "You can paste text or upload PDF documents. ProofLoop AI checks "
    "for exact sentence matches and certain simple contradictions, "
    "and provides semantic similarity assessments to help review evidence."
)

st.caption(
    "Prototype limitation: this application analyzes the text you "
    "provide or extract from PDFs. Semantic similarity measures textual "
    "resemblance; it does not establish factual correctness. The verifier "
    "does not independently authenticate sources. Scanned PDFs can use OCR "
    "when Tesseract is installed. OCR may misread text, so review extracted "
    "evidence carefully."
)


# --------------------------------------------------
# 1. Enter claim
# --------------------------------------------------

st.header("1. Enter your claim")

claim = st.text_area(
    "Claim",
    placeholder="Enter the claim you want to verify...",
)


# --------------------------------------------------
# 2. Add evidence sources
# --------------------------------------------------

st.header("2. Add evidence sources")

source_count = st.number_input(
    "Number of sources",
    min_value=1,
    max_value=5,
    value=2,
    step=1,
)

sources = []

for i in range(int(source_count)):
    st.markdown(f"**Source {i + 1}**")

    name = st.text_input(
        "Source name",
        value=f"Source {i + 1}",
        key=f"name_{i}",
    )

    evidence_method = st.radio(
        "Evidence input method",
        ["Paste text", "Upload PDF"],
        horizontal=True,
        key=f"method_{i}",
    )

    evidence_text = ""

    if evidence_method == "Paste text":
        evidence_text = st.text_area(
            "Evidence text",
            placeholder="Paste evidence here...",
            key=f"evidence_{i}",
        )

    else:
        uploaded_pdf = st.file_uploader(
            "Upload a PDF document",
            type=["pdf"],
            key=f"pdf_{i}",
        )

        if uploaded_pdf is not None:
            try:
                pdf_result = extract_text_from_pdf(
                    uploaded_pdf.getvalue()
                )

                st.caption(
                    f"PDF pages: {pdf_result['page_count']}"
                )

                if pdf_result["has_text"]:
                    evidence_text = pdf_result["text"]

                    st.success("Text extracted from PDF.")

                    with st.expander("Preview extracted text"):
                        st.text(evidence_text[:10000])

                        if len(evidence_text) > 10000:
                            st.caption(
                                "Preview limited to the first 10,000 "
                                "characters. Full extracted text is "
                                "used for verification."
                            )

                else:
                    st.warning(
                        "No text could be extracted from this PDF. "
                        "It may be blank, scanned, or image-based. "
                        "Check that Tesseract OCR is installed and "
                        "that the PDF contains readable text."
                    )

            except Exception as error:
                st.error(
                    f"Could not process this PDF: {error}"
                )

    sources.append({
        "source_id": f"source_{i + 1:03d}",
        "source_name": name,
        "text": evidence_text,
    })


# --------------------------------------------------
# 3. Verify claim
# --------------------------------------------------

if st.button("Verify claim", type="primary"):

    if not claim.strip():
        st.error("Please enter a claim.")
        st.stop()

    evidence_records = []

    for source in sources:
        if source["text"].strip():
            try:
                record = create_evidence_record(
                    source["source_id"],
                    source["source_name"],
                    source["text"],
                )

                evidence_records.append(record)

            except (ValueError, TypeError) as error:
                st.error(
                    f"Could not create evidence record: {error}"
                )
                st.stop()

    if not evidence_records:
        st.error(
            "Please provide evidence using text or a PDF "
            "with extractable text."
        )
        st.stop()

    # Run existing verification rules.
    # Semantic similarity does not determine these verdicts.
    result = verify_claim_against_sources(
        claim,
        evidence_records,
    )

    report = create_verification_report(result)

    # --------------------------------------------------
    # 4. Semantic similarity assessment
    # --------------------------------------------------

    semantic_scores = []

    with st.spinner("Analyzing semantic similarity..."):

        for source in evidence_records:
            source_id = source["source_id"]
            source_name = source["source_name"]
            source_text = source["text"]

            try:
                score = calculate_similarity(
                    claim,
                    source_text,
                )

                if score >= SEMANTIC_REVIEW_THRESHOLD:
                    assessment = "POSSIBLE_PARAPHRASE"

                    assessment_reason = (
                        "The text has relatively high semantic similarity "
                        "to the claim. Manually review whether it actually "
                        "supports, contradicts, or merely discusses the claim."
                    )

                else:
                    assessment = "LOW_SIMILARITY"

                    assessment_reason = (
                        "The text did not reach the configured similarity "
                        "threshold. This does not prove that the evidence "
                        "is irrelevant or unrelated."
                    )

                semantic_scores.append({
                    "source_id": source_id,
                    "source_name": source_name,
                    "similarity": score,
                    "assessment": assessment,
                    "assessment_reason": assessment_reason,
                })

            except Exception as error:
                st.warning(
                    f"Semantic similarity unavailable for "
                    f"{source_name}: {error}"
                )

                semantic_scores.append({
                    "source_id": source_id,
                    "source_name": source_name,
                    "similarity": None,
                    "assessment": "UNAVAILABLE",
                    "assessment_reason": (
                        "The semantic assessment could not be calculated."
                    ),
                })

    # Add supplementary assessments to the report.
    # Original verification verdicts remain unchanged.
    report["semantic_scores"] = semantic_scores

    # Export the complete report, including semantic assessments.
    try:
        json_report = export_report_json(report)

    except (ValueError, TypeError) as error:
        st.error(f"Could not export the report: {error}")
        st.stop()

    # Save the results so they remain visible after Streamlit reruns.
    st.session_state["report"] = report
    st.session_state["json_report"] = json_report


# --------------------------------------------------
# 5. Display verification report
# --------------------------------------------------

if "report" in st.session_state:

    report = st.session_state["report"]

    st.divider()
    st.header("3. Verification report")

    status = report["overall_status"]

    if status == "SUPPORTED":
        st.success(f"Verdict: {status}")

    elif status == "CONTRADICTED":
        st.error(f"Verdict: {status}")

    else:
        st.warning(f"Verdict: {status}")

    st.write("**Claim:**", report["claim"])
    st.write("**Summary:**", report["summary"])

    col1, col2 = st.columns(2)

    col1.metric(
        "Evidence sources",
        report["source_count"],
    )

    col2.metric(
        "Conflicting sources",
        "Yes" if report["has_conflicting_sources"] else "No",
    )

    for warning in report["warnings"]:
        st.warning(warning)


    # --------------------------------------------------
    # 6. Display semantic assessments
    # --------------------------------------------------

    st.subheader("Semantic similarity analysis")

    st.caption(
        "Higher similarity scores indicate greater textual resemblance. "
        "POSSIBLE_PARAPHRASE is a review signal, not a factual verdict. "
        "LOW_SIMILARITY does not rule out relevant evidence. The threshold "
        "is a configurable heuristic, not a scientifically established "
        "boundary between related and unrelated claims."
    )

    for item in report.get("semantic_scores", []):

        with st.container(border=True):

            st.write(f"**{item['source_name']}**")

            score = item["similarity"]

            if score is None:
                st.warning(
                    "A similarity score could not be calculated."
                )

            else:
                # Progress bars accept values from 0 to 1.
                # Preserve the original score for the displayed number.
                st.progress(
                    max(0.0, min(1.0, score))
                )

                st.write(
                    f"Similarity score: **{score:.3f}**"
                )

            assessment = item["assessment"]

            if assessment == "POSSIBLE_PARAPHRASE":
                st.info(
                    "Assessment: POSSIBLE_PARAPHRASE"
                )

            elif assessment == "LOW_SIMILARITY":
                st.caption(
                    "Assessment: LOW_SIMILARITY"
                )

            else:
                st.warning(
                    "Assessment: UNAVAILABLE"
                )

            st.write(item["assessment_reason"])


    # --------------------------------------------------
    # 7. Source-by-source verification results
    # --------------------------------------------------

    st.subheader("Source-by-source results")

    for i, source in enumerate(
        report["sources"],
        start=1,
    ):

        with st.expander(
            f"{i}. {source['source_name']} - {source['status']}"
        ):

            st.write(
                "**Source ID:**",
                source["source_id"],
            )

            st.write(
                "**Verdict:**",
                source["status"],
            )

            st.write(
                "**Reason:**",
                source["reason"],
            )

            st.write(
                "**Evidence:**",
                source["evidence_text"],
            )


    # --------------------------------------------------
    # 8. Download and preview JSON
    # --------------------------------------------------

    st.subheader("Export report")

    st.download_button(
        "Download JSON report",
        data=st.session_state["json_report"],
        file_name="proofloop_verification_report.json",
        mime="application/json",
    )

    with st.expander("Preview JSON report"):

        st.code(
            st.session_state["json_report"],
            language="json",
        )
