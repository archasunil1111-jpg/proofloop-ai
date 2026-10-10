
import streamlit as st

from src.verifier import (
    create_evidence_record,
    verify_claim_against_sources,
    create_verification_report,
    export_report_json,
)

st.set_page_config(page_title="ProofLoop AI", page_icon="🔎", layout="wide")

st.title("🔎 ProofLoop AI")
st.subheader("Evidence-based claim verification")

st.write(
    "Enter a claim and provide evidence from different sources. "
    "ProofLoop AI checks for exact sentence matches and certain simple "
    "contradictions. Unclear results are marked for manual review."
)

st.caption(
    "Prototype limitation: this version checks the text you provide. "
    "It does not independently verify source authenticity or establish "
    "whether a claim is factually true."
)

st.header("1. Enter your claim")
claim = st.text_area(
    "Claim",
    placeholder="Enter the claim you want to verify...",
)

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

    evidence = st.text_area(
        "Evidence text",
        placeholder="Paste evidence here...",
        key=f"evidence_{i}",
    )

    sources.append({
        "source_id": f"source_{i + 1:03d}",
        "source_name": name,
        "text": evidence,
    })

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
            except ValueError as error:
                st.error(str(error))
                st.stop()

    if not evidence_records:
        st.error("Please provide evidence for at least one source.")
        st.stop()

    result = verify_claim_against_sources(claim, evidence_records)
    report = create_verification_report(result)
    json_report = export_report_json(report)

    st.session_state["report"] = report
    st.session_state["json_report"] = json_report

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
    col1.metric("Evidence sources", report["source_count"])
    col2.metric(
        "Conflicting sources",
        "Yes" if report["has_conflicting_sources"] else "No",
    )

    for warning in report["warnings"]:
        st.warning(warning)

    st.subheader("Source-by-source results")

    for i, source in enumerate(report["sources"], start=1):
        with st.expander(f"{i}. {source['source_name']} - {source['status']}"):
            st.write("**Source ID:**", source["source_id"])
            st.write("**Verdict:**", source["status"])
            st.write("**Reason:**", source["reason"])
            st.write("**Evidence:**", source["evidence_text"])

    st.download_button(
        "Download JSON report",
        data=st.session_state["json_report"],
        file_name="proofloop_verification_report.json",
        mime="application/json",
    )

    with st.expander("Preview JSON report"):
        st.code(st.session_state["json_report"], language="json")
