
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


def verify_claim(claim: str, evidence: str) -> dict[str, str]:
    """Verify a claim using conservative, exact sentence matching."""

    if not claim.strip():
        raise ValueError("Claim cannot be empty.")

    if not evidence.strip():
        return {
            "claim": claim,
            "status": "UNVERIFIABLE",
            "reason": "No evidence was provided.",
        }

    normalized_claim = _normalize(claim)
    evidence_sentences = _split_sentences(evidence)

    opposite_claim = _opposite_copula_claim(normalized_claim)

    has_support = normalized_claim in evidence_sentences
    has_contradiction = (
        opposite_claim is not None
        and opposite_claim in evidence_sentences
    )

    # Conflicting exact matches must not produce a confident verdict.
    if has_support and has_contradiction:
        return {
            "claim": claim,
            "status": "UNVERIFIABLE",
            "reason": (
                "The evidence contains both supporting and opposing "
                "statements. Manual review is required."
            ),
        }

    if has_contradiction:
        return {
            "claim": claim,
            "status": "CONTRADICTED",
            "reason": (
                "A complete evidence sentence matches a simple "
                "opposite-polarity form. Review the source before relying on it."
            ),
        }

    if has_support:
        return {
            "claim": claim,
            "status": "SUPPORTED",
            "reason": (
                "A complete evidence sentence matches the claim "
                "after normalizing capitalization and punctuation."
            ),
        }

    return {
        "claim": claim,
        "status": "UNVERIFIABLE",
        "reason": (
            "No complete sentence match or recognized simple contradiction "
            "was found. This does not establish whether the claim is true."
        ),
    }


if __name__ == "__main__":
    examples = [
        ("Python is popular.", "Python is popular."),
        ("Python is popular.", "Python is not popular."),
        (
            "Python is popular.",
            "Python is popular in some regions, but usage varies.",
        ),
    ]

    for claim, evidence in examples:
        print(verify_claim(claim, evidence))
