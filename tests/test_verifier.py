
import sys
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

from verifier import verify_claim


class TestVerifyClaim(unittest.TestCase):

    def test_empty_claim_raises_error(self):
        with self.assertRaises(ValueError):
            verify_claim("", "Python is popular.")

    def test_empty_evidence_is_unverifiable(self):
        result = verify_claim("Python is popular.", "")

        self.assertEqual(result["status"], "UNVERIFIABLE")

    def test_direct_match_is_supported(self):
        result = verify_claim(
            "Python is popular.",
            "Python is popular.",
        )

        self.assertEqual(result["status"], "SUPPORTED")

    def test_simple_opposite_polarity_is_contradicted(self):
        result = verify_claim(
            "Python is popular.",
            "Python is not popular.",
        )

        self.assertEqual(result["status"], "CONTRADICTED")

    def test_unrelated_evidence_is_unverifiable(self):
        result = verify_claim(
            "Python is popular.",
            "Python is used for data science.",
        )

        self.assertEqual(result["status"], "UNVERIFIABLE")

    def test_matching_is_case_insensitive(self):
        result = verify_claim(
            "Python is popular.",
            "PYTHON IS POPULAR.",
        )

        self.assertEqual(result["status"], "SUPPORTED")


if __name__ == "__main__":
    unittest.main()
