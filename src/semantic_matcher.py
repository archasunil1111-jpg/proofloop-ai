
"""Semantic similarity utilities for ProofLoop AI."""

from functools import lru_cache

from sentence_transformers import SentenceTransformer, util


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def load_model() -> SentenceTransformer:
    """Load and cache the sentence embedding model."""
    return SentenceTransformer(MODEL_NAME)


def calculate_similarity(claim: str, evidence: str) -> float:
    """Return cosine similarity between a claim and evidence text."""
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Claim must not be empty.")

    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError("Evidence must not be empty.")

    model = load_model()

    embeddings = model.encode(
        [claim.strip(), evidence.strip()],
        convert_to_tensor=True,
        normalize_embeddings=True,
    )

    score = util.cos_sim(embeddings[0], embeddings[1]).item()

    return float(score)
