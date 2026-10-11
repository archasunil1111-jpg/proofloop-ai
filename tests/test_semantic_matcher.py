
import unittest
from unittest.mock import patch

from src.semantic_matcher import calculate_similarity


class TestSemanticMatcher(unittest.TestCase):

    def test_similar_sentences_have_high_similarity(self):
        score = calculate_similarity(
            "The Earth revolves around the Sun.",
            "Earth orbits our star, the Sun.",
        )

        self.assertGreater(score, 0.60)
        self.assertLessEqual(score, 1.0)

    def test_empty_claim_raises_error(self):
        with self.assertRaises(ValueError):
            calculate_similarity("", "Some evidence.")

    def test_empty_evidence_raises_error(self):
        with self.assertRaises(ValueError):
            calculate_similarity("Some claim.", "   ")

    def test_similarity_returns_float(self):
        score = calculate_similarity(
            "The Earth revolves around the Sun.",
            "Earth orbits our star, the Sun.",
        )

        self.assertIsInstance(score, float)


if __name__ == "__main__":
    unittest.main()
