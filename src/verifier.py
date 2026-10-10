
import re
from typing import Literal


VerificationStatus = Literal[
    "SUPPORTED",
    "CONTRADICTED",
    "UNVERIFIABLE",
]


def _normalize(text: str) -> str:
    """Normalize text for simple, case-insensitive matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return " ".join(text.split())


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
    """Check a claim against evidence using conservative text rules."""

    if not claim.strip():
        raise ValueError("Claim cannot be empty.")

    if not evidence.strip():
        return {
            "claim": claim,
            "status": "UNVERIFIABLE",
            "reason": "No evidence was provided.",
        }

    normalized_claim = _normalize(claim)
    normalized_evidence = _normalize(evidence)

    # Check explicit opposite polarity before direct matching.
    opposite_claim = _opposite_copula_claim(normalized_claim)

    if (
        opposite_claim
        and re.search(
            r"(?<!\w)" + re.escape(opposite_claim) + r"(?!\w)",
            normalized_evidence,
        )
    ):
        return {
            "claim": claim,
            "status": "CONTRADICTED",
            "reason": (
                "The evidence contains a simple opposite-polarity "
                "statement. Review the source before relying on it."
            ),
        }

    if re.search(
        r"(?<!\w)" + re.escape(normalized_claim) + r"(?!\w)",
        normalized_evidence,
    ):
        return {
            "claim": claim,
            "status": "SUPPORTED",
            "reason": "The claim text appears directly in the evidence.",
        }

    return {
        "claim": claim,
        "status": "UNVERIFIABLE",
        "reason": (
            "No direct match or recognized simple contradiction "
            "was found. This does not establish whether the claim is true."
        ),
    }
