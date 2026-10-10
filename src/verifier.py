
import re
from typing import Literal


VerificationStatus = Literal[
    "SUPPORTED",
    "CONTRADICTED",
    "UNVERIFIABLE",
]


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

    has_support = normalized_claim in evidence_sentences

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
                "A complete evidence sentence matches the claim after "
                "normalizing capitalization and punctuation."
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
) -> dict:
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
        reason = "At least one source contradicts the claim, and none supports it."

    elif "SUPPORTED" in statuses and "CONTRADICTED" not in statuses:
        overall_status = "SUPPORTED"
        reason = "At least one source supports the claim, with no recognized contradiction."

    else:
        overall_status = "UNVERIFIABLE"
        reason = "The available source results do not establish a reliable verdict."

    return {
        "claim": claim,
        "status": overall_status,
        "reason": reason,
        "source_results": source_results,
    }


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

    print(
        verify_claim_against_sources(
            "Python is popular.",
            example_sources,
        )
    )
