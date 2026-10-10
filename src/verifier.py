
import re
from typing import Literal


VerificationStatus = Literal[
    "SUPPORTED",
    "CONTRADICTED",
    "UNVERIFIABLE",
]


def _normalize(text: str) -> str:
    """Normalize text for case-insensitive matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return " ".join(text.split())


def _split_sentences(text: str) -> list[str]:
    """Split evidence into sentences and normalize each sentence."""
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [_normalize(part) for part in parts if part.strip()]


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
    """
    Verify a claim using conservative sentence-level text rules.

    source_id identifies the source associated with the supplied evidence.
    This function does not independently verify the source's authenticity.
    """

    if not claim.strip():
        raise ValueError("Claim cannot be empty.")

    if not evidence.strip():
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
                "A complete evidence sentence matches the claim "
                "after normalizing capitalization and punctuation."
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


if __name__ == "__main__":
    examples = [
        (
            "Python is popular.",
            "Python is popular.",
            "article_001",
        ),
        (
            "Python is popular.",
            "Python is not popular.",
            "report_002",
        ),
        (
            "Python is popular.",
            "The sky is blue.",
            "report_003",
        ),
    ]

    for claim, evidence, source_id in examples:
        print(verify_claim(claim, evidence, source_id))
