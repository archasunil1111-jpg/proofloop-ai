
from typing import Literal


VerificationStatus = Literal[
    "SUPPORTED",
    "CONTRADICTED",
    "UNVERIFIABLE",
]


def verify_claim(
    claim: str,
    evidence: str,
) -> dict[str, str]:
    """Check a claim against explicitly supplied evidence."""

    if not claim.strip():
        raise ValueError("Claim cannot be empty.")

    if not evidence.strip():
        return {
            "claim": claim,
            "status": "UNVERIFIABLE",
            "reason": "No evidence was provided.",
        }

    # Initial safe baseline: do not pretend that
    # matching words proves that a claim is true.
    return {
        "claim": claim,
        "status": "UNVERIFIABLE",
        "reason": (
            "Evidence received. Semantic verification "
            "will be added in a later development stage."
        ),
    }
