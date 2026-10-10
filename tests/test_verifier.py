
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
            verify_claim("", "Python is a programming language.")

    def test_empty_evidence_is_unverifiable(self):
        result = verify_claim("Python is popular.", "")

        self.assertEqual(result["status"], "UNVERIFIABLE")
        self.assertIn("No evidence", result["reason"])

    def test_nonempty_inputs_are_not_assumed_true(self):
        result = verify_claim(
            "Python is popular.",
            "Python is used for data science.",
        )

        self.assertEqual(result["status"], "UNVERIFIABLE")
        self.assertEqual(result["claim"], "Python is popular.")


if __name__ == "__main__":
    unittest.main()
