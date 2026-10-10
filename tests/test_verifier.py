
import unittest

from src.verifier import (
    create_evidence_record,
    verify_claim,
    verify_claim_against_sources,
)


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
            "Python is popular. Python is not popular in this example.",
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
            "article_001",
            "Python Report",
            "Python is popular.",
        )
        self.assertEqual(evidence["source_id"], "article_001")
        self.assertEqual(evidence["source_name"], "Python Report")
        self.assertEqual(evidence["text"], "Python is popular.")

    def test_evidence_record_strips_extra_whitespace(self):
        evidence = create_evidence_record(
            "  article_001  ",
            "  Python Report  ",
            "  Python is popular.  ",
        )
        self.assertEqual(evidence["source_id"], "article_001")
        self.assertEqual(evidence["source_name"], "Python Report")
        self.assertEqual(evidence["text"], "Python is popular.")

    def test_evidence_record_rejects_blank_source_id(self):
        with self.assertRaises(ValueError):
            create_evidence_record(
                " ",
                "Python Report",
                "Python is popular.",
            )

    def test_evidence_record_rejects_blank_source_name(self):
        with self.assertRaises(ValueError):
            create_evidence_record(
                "article_001",
                " ",
                "Python is popular.",
            )

    def test_evidence_record_rejects_blank_text(self):
        with self.assertRaises(ValueError):
            create_evidence_record(
                "article_001",
                "Python Report",
                " ",
            )

    def test_multiple_sources_all_support_claim(self):
        sources = [
            create_evidence_record(
                "source_001",
                "Source One",
                "Python is popular.",
            ),
            create_evidence_record(
                "source_002",
                "Source Two",
                "Python is popular.",
            ),
        ]

        result = verify_claim_against_sources(
            "Python is popular.",
            sources,
        )

        self.assertEqual(result["status"], "SUPPORTED")
        self.assertEqual(len(result["source_results"]), 2)

    def test_multiple_sources_with_conflicting_evidence(self):
        sources = [
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

        result = verify_claim_against_sources(
            "Python is popular.",
            sources,
        )

        self.assertEqual(result["status"], "UNVERIFIABLE")
        self.assertEqual(len(result["source_results"]), 2)

    def test_multiple_sources_with_no_support_are_unverifiable(self):
        sources = [
            create_evidence_record(
                "source_001",
                "Source One",
                "The sky is blue.",
            ),
            create_evidence_record(
                "source_002",
                "Source Two",
                "Water is wet.",
            ),
        ]

        result = verify_claim_against_sources(
            "Python is popular.",
            sources,
        )

        self.assertEqual(result["status"], "UNVERIFIABLE")

    def test_multiple_sources_empty_list_is_unverifiable(self):
        result = verify_claim_against_sources(
            "Python is popular.",
            [],
        )

        self.assertEqual(result["status"], "UNVERIFIABLE")


if __name__ == "__main__":
    unittest.main()
