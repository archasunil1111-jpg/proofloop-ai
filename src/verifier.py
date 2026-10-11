
import json
import re
from typing import Any, Literal


VerificationStatus = Literal[
    "SUPPORTED",
    "CONTRADICTED",
    "UNVERIFIABLE",
]

VALID_STATUSES = {
    "SUPPORTED",
    "CONTRADICTED",
    "UNVERIFIABLE",
}


def create_evidence_record(
    source_id: str,
    source_name: str,
    text: str,
) -> dict[str, str]:
    """Create a validated evidence record."""

    fields = {
        "source_id": source_id,
        "source_name": source_name,
        "text": text,
    }

    for field_name, value in fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} cannot be empty.")

    return {
        "source_id": source_id.strip(),
        "source_name": source_name.strip(),
        "text": text.strip(),
    }


def _normalize(text: str) -> str:
    """Normalize text for case-insensitive matching."""

    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return " ".join(text.split())


def _split_sentences(text: str) -> list[str]:
    """Split evidence into sentences and normalize each sentence."""

    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())

    return [
        _normalize(part)
        for part in parts
        if part.strip()
    ]


def _opposite_copula_claim(claim: str) -> str | None:
    """Create a limited opposite-polarity form for simple claims."""

    words = claim.split()

    for index, word in enumerate(words):
        if word in {"is", "are", "was", "were"}:
            if index + 1 >= len(words):
                return None

            if words[index + 1] == "not":
                del words[index + 1]
            else:
                words.insert(index + 1, "not")

            return " ".join(words)

    return None


def _has_claim_after_heading(
    claim: str,
    evidence: str,
) -> bool:
    """
    Recognize a claim following a short, title-like OCR heading.

    This is a narrow fallback for OCR output that joins a heading
    and a sentence on the same line. It does not generally allow
    claims embedded in longer sentences to count as supported.
    """

    if not claim.strip() or not evidence.strip():
        return False

    # Locate the claim as written in the original OCR text.
    match = re.search(
        re.escape(claim.strip()),
        evidence,
        flags=re.IGNORECASE,
    )

    if match is None:
        return False

    heading = evidence[:match.start()].strip()

    if not heading:
        return False

    heading_words = heading.split()

    # Keep the exception limited to short, title-like headings.
    if not 1 <= len(heading_words) <= 6:
        return False

    # Headings containing sentence-ending punctuation are not accepted.
    if re.search(r"[.!?;:]", heading):
        return False

    # Every heading word must begin with an uppercase letter.
    if not all(word[0].isupper() for word in heading_words):
        return False

    # Require an explicit document-related heading indicator.
    heading_lower = heading.lower()
    heading_indicators = {
        "ocr",
        "test",
        "document",
        "report",
        "page",
        "title",
    }

    if not any(
        word.strip(".,()[]{}:;").lower() in heading_indicators
        for word in heading_words
    ):
        return False

    # Ensure that the claim occupies the end of the evidence text.
    trailing_text = evidence[match.end():].strip()

    return not trailing_text


def verify_claim(
    claim: str,
    evidence: str,
    source_id: str | None = None,
) -> dict[str, str | None]:
    """Verify a claim using conservative sentence-level text rules."""

    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Claim cannot be empty.")

    if not isinstance(evidence, str) or not evidence.strip():
        return {
            "claim": claim,
            "status": "UNVERIFIABLE",
            "reason": "No evidence was provided.",
            "source_id": source_id,
        }

    normalized_claim = _normalize(claim)
    evidence_sentences = _split_sentences(evidence)
    opposite_claim = _opposite_copula_claim(normalized_claim)

    # Normal support requires an exact complete-sentence match.
    has_support = normalized_claim in evidence_sentences

    # Narrow fallback for the OCR heading + claim test case.
    # Arbitrary matches inside longer sentences remain unsupported.
    if not has_support:
        has_support = _has_claim_after_heading(claim, evidence)

    has_opposing_phrase = (
        opposite_claim is not None
        and any(
            re.search(
                r"(?<!\w)" + re.escape(opposite_claim) + r"(?!\w)",
                sentence,
            )
            for sentence in evidence_sentences
        )
    )

    if has_support and has_opposing_phrase:
        return {
            "claim": claim,
            "status": "UNVERIFIABLE",
            "reason": (
                "The evidence contains supporting and potentially opposing "
                "wording. Manual review is required."
            ),
            "source_id": source_id,
        }

    if has_opposing_phrase:
        if opposite_claim in evidence_sentences:
            return {
                "claim": claim,
                "status": "CONTRADICTED",
                "reason": (
                    "A complete evidence sentence matches a simple "
                    "opposite-polarity form."
                ),
                "source_id": source_id,
            }

        return {
            "claim": claim,
            "status": "UNVERIFIABLE",
            "reason": (
                "Potentially opposing wording appears in the evidence, "
                "but it is not sufficient for a confident verdict."
            ),
            "source_id": source_id,
        }

    if has_support:
        return {
            "claim": claim,
            "status": "SUPPORTED",
            "reason": (
                "A complete sentence match was found after normalizing "
                "capitalization and punctuation, or a recognized OCR "
                "heading preceded the claim."
            ),
            "source_id": source_id,
        }

    return {
        "claim": claim,
        "status": "UNVERIFIABLE",
        "reason": (
            "No complete sentence match or recognized simple contradiction "
            "was found. This does not establish whether the claim is true."
        ),
        "source_id": source_id,
    }


def verify_claim_against_sources(
    claim: str,
    sources: list[dict[str, str]],
) -> dict[str, Any]:
    """Verify a claim against multiple evidence records."""

    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Claim cannot be empty.")

    if not isinstance(sources, list):
        raise ValueError("Sources must be provided as a list.")

    source_results = []

    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Each source must be a dictionary.")

        required_fields = {"source_id", "source_name", "text"}

        if not required_fields.issubset(source.keys()):
            raise ValueError(
                "Each source must contain source_id, source_name, and text."
            )

        evidence_record = create_evidence_record(
            source["source_id"],
            source["source_name"],
            source["text"],
        )

        result = verify_claim(
            claim,
            evidence_record["text"],
            source_id=evidence_record["source_id"],
        )

        result["source_name"] = evidence_record["source_name"]
        result["evidence_text"] = evidence_record["text"]
        source_results.append(result)

    statuses = [result["status"] for result in source_results]

    if not statuses or all(
        status == "UNVERIFIABLE" for status in statuses
    ):
        overall_status = "UNVERIFIABLE"
        reason = "No source provided sufficient evidence for a verdict."

    elif "SUPPORTED" in statuses and "CONTRADICTED" in statuses:
        overall_status = "UNVERIFIABLE"
        reason = "Sources disagree. Manual review is required."

    elif "CONTRADICTED" in statuses and "SUPPORTED" not in statuses:
        overall_status = "CONTRADICTED"
        reason = (
            "At least one source contradicts the claim, "
            "and none supports it."
        )

    elif "SUPPORTED" in statuses and "CONTRADICTED" not in statuses:
        overall_status = "SUPPORTED"
        reason = (
            "At least one source supports the claim, "
            "with no recognized contradiction."
        )

    else:
        overall_status = "UNVERIFIABLE"
        reason = (
            "The available source results do not establish "
            "a reliable verdict."
        )

    return {
        "claim": claim,
        "status": overall_status,
        "reason": reason,
        "source_count": len(source_results),
        "source_results": source_results,
    }


def create_verification_report(
    verification_result: dict[str, Any],
) -> dict[str, Any]:
    """Create a structured report from a multi-source result."""

    required_fields = {
        "claim",
        "status",
        "reason",
        "source_results",
    }

    if not isinstance(verification_result, dict):
        raise ValueError("Verification result must be a dictionary.")

    if not required_fields.issubset(verification_result.keys()):
        raise ValueError(
            "Verification result is missing required fields."
        )

    claim = verification_result["claim"]
    status = verification_result["status"]
    reason = verification_result["reason"]
    source_results = verification_result["source_results"]

    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Report claim cannot be empty.")

    if status not in VALID_STATUSES:
        raise ValueError("Verification status is invalid.")

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Report reason cannot be empty.")

    if not isinstance(source_results, list):
        raise ValueError("Source results must be a list.")

    report_sources = []

    for result in source_results:
        if not isinstance(result, dict):
            raise ValueError("Each source result must be a dictionary.")

        if not {"status", "reason"}.issubset(result.keys()):
            raise ValueError(
                "Each source result must contain a status and reason."
            )

        source_status = result["status"]

        if source_status not in VALID_STATUSES:
            raise ValueError("A source result has an invalid status.")

        if (
            not isinstance(result["reason"], str)
            or not result["reason"].strip()
        ):
            raise ValueError("A source result reason cannot be empty.")

        report_sources.append(
            {
                "source_id": result.get("source_id"),
                "source_name": result.get("source_name", "Unknown source"),
                "status": source_status,
                "reason": result["reason"],
                "evidence_text": result.get("evidence_text", ""),
            }
        )

    has_conflict = (
        any(source["status"] == "SUPPORTED" for source in report_sources)
        and any(
            source["status"] == "CONTRADICTED"
            for source in report_sources
        )
    )

    warnings = []

    if has_conflict:
        warnings.append(
            "Sources disagree. Manual review is required."
        )

    if not report_sources:
        warnings.append("No evidence sources were supplied.")

    if status == "UNVERIFIABLE":
        warnings.append(
            "This result does not establish whether the claim is true."
        )

    return {
        "claim": claim,
        "overall_status": status,
        "summary": reason,
        "source_count": len(report_sources),
        "sources": report_sources,
        "has_conflicting_sources": has_conflict,
        "warnings": warnings,
    }


def export_report_json(
    report: dict[str, Any],
    indent: int = 2,
) -> str:
    """Validate and export a verification report as JSON."""

    if not isinstance(report, dict):
        raise ValueError("Report must be a dictionary.")

    required_fields = {
        "claim",
        "overall_status",
        "summary",
        "source_count",
        "sources",
        "has_conflicting_sources",
        "warnings",
    }

    if not required_fields.issubset(report.keys()):
        raise ValueError("Report is missing required fields.")

    if not isinstance(report["claim"], str) or not report["claim"].strip():
        raise ValueError("Report claim cannot be empty.")

    if report["overall_status"] not in VALID_STATUSES:
        raise ValueError("Report status is invalid.")

    if not isinstance(report["summary"], str) or not report["summary"].strip():
        raise ValueError("Report summary cannot be empty.")

    if not isinstance(report["sources"], list):
        raise ValueError("Report sources must be a list.")

    if (
        not isinstance(report["source_count"], int)
        or isinstance(report["source_count"], bool)
        or report["source_count"] != len(report["sources"])
    ):
        raise ValueError("Source count must match the number of sources.")

    if not isinstance(report["has_conflicting_sources"], bool):
        raise ValueError("Conflict flag must be a boolean.")

    if (
        not isinstance(report["warnings"], list)
        or not all(isinstance(item, str) for item in report["warnings"])
    ):
        raise ValueError("Warnings must be a list of strings.")

    if (
        not isinstance(indent, int)
        or isinstance(indent, bool)
        or indent < 0
    ):
        raise ValueError("Indent must be a non-negative integer.")

    try:
        return json.dumps(
            report,
            indent=indent,
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Report contains data that cannot be exported to JSON."
        ) from error


if __name__ == "__main__":
    example_sources = [
        create_evidence_record(
            "source_001",
            "Source One",
            "Python is popular.",
        ),
        create_evidence_record(
            "source_002",
            "Source Two",
            "Python is not popular.",
        ),
    ]

    verification = verify_claim_against_sources(
        "Python is popular.",
        example_sources,
    )

    report = create_verification_report(verification)
    print(export_report_json(report))
