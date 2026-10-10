
import unittest

from src.verifier import create_evidence_record, verify_claim


class TestVerifyClaim(unittest.TestCase):

    def test_empty_claim_raises_error(self):
        with self.assertRaises(ValueError):
            verify_claim("", "Python is popular.")

    def test_empty_evidence_is_unverifiable(self):
        result = verify_claim(
            "Python is popular.",
            "",
        )
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
            "The sky is blue.",
        )
        self.assertEqual(result["status"], "UNVERIFIABLE")

    def test_matching_is_case_insensitive(self):
        result = verify_claim(
            "Python is popular.",
            "PYTHON IS POPULAR.",
        )
        self.assertEqual(result["status"], "SUPPORTED")

    def test_claim_inside_longer_sentence_is_not_automatically_supported(self):
        result = verify_claim(
            "Python is popular.",
            "Python is popular in some regions.",
        )
        self.assertEqual(result["status"], "UNVERIFIABLE")

    def test_contradiction_inside_mixed_evidence_is_unverifiable(self):
        result = verify_claim(
            "Python is popular.",
            "Python is popular. Python is not popular.",
        )
        self.assertEqual(result["status"], "UNVERIFIABLE")

    def test_punctuation_difference_does_not_break_direct_match(self):
        result = verify_claim(
            "Python is popular!",
            "Python is popular.",
        )
        self.assertEqual(result["status"], "SUPPORTED")

    def test_supporting_sentence_with_qualified_contradiction_is_unverifiable(self):
        result = verify_claim(
            "Python is popular.",
            (
                "Python is popular. "
                "Python is not popular in this example."
            ),
        )
        self.assertEqual(result["status"], "UNVERIFIABLE")

    def test_source_id_is_preserved_for_supported_claim(self):
        result = verify_claim(
            "Python is popular.",
            "Python is popular.",
            source_id="article_001",
        )

        self.assertEqual(result["status"], "SUPPORTED")
        self.assertEqual(result["source_id"], "article_001")

    def test_source_id_is_preserved_for_unverifiable_claim(self):
        result = verify_claim(
            "Python is popular.",
            "The sky is blue.",
            source_id="report_002",
        )

        self.assertEqual(result["status"], "UNVERIFIABLE")
        self.assertEqual(result["source_id"], "report_002")

    def test_evidence_record_preserves_source_details(self):
        evidence = create_evidence_record(
            source_id="article_001",
            source_name="Python Report",
            text="Python is popular.",
        )

        self.assertEqual(evidence["source_id"], "article_001")
        self.assertEqual(evidence["source_name"], "Python Report")
        self.assertEqual(evidence["text"], "Python is popular.")

    def test_evidence_record_strips_extra_whitespace(self):
        evidence = create_evidence_record(
            source_id="  article_001  ",
            source_name="  Python Report  ",
            text="  Python is popular.  ",
        )

        self.assertEqual(evidence["source_id"], "article_001")
        self.assertEqual(evidence["source_name"], "Python Report")
        self.assertEqual(evidence["text"], "Python is popular.")

    def test_evidence_record_rejects_blank_source_id(self):
        with self.assertRaises(ValueError):
            create_evidence_record(
                source_id=" ",
                source_name="Python Report",
                text="Python is popular.",
            )

    def test_evidence_record_rejects_blank_source_name(self):
        with self.assertRaises(ValueError):
            create_evidence_record(
                source_id="article_001",
                source_name=" ",
                text="Python is popular.",
            )

    def test_evidence_record_rejects_blank_text(self):
        with self.assertRaises(ValueError):
            create_evidence_record(
                source_id="article_001",
                source_name="Python Report",
                text=" ",
            )


if __name__ == "__main__":
    unittest.main()
