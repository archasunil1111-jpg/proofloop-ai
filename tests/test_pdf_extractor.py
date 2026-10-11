
import unittest
from io import BytesIO
from unittest.mock import patch, MagicMock

from pypdf import PdfWriter

from src.pdf_extractor import extract_text_from_pdf


def create_test_pdf():
    """Create a blank PDF in memory for testing."""
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class TestPDFExtractor(unittest.TestCase):

    def test_extracts_page_count(self):
        pdf_bytes = create_test_pdf()
        result = extract_text_from_pdf(pdf_bytes)

        self.assertEqual(result["page_count"], 1)
        self.assertEqual(len(result["pages"]), 1)

    def test_returns_expected_result_fields(self):
        pdf_bytes = create_test_pdf()
        result = extract_text_from_pdf(pdf_bytes)

        self.assertIn("page_count", result)
        self.assertIn("pages", result)
        self.assertIn("text", result)
        self.assertIn("has_text", result)

    def test_blank_pdf_has_no_extractable_text(self):
        pdf_bytes = create_test_pdf()
        result = extract_text_from_pdf(pdf_bytes)

        self.assertFalse(result["has_text"])
        self.assertEqual(result["text"], "")

    def test_normalizes_pdf_line_breaks_and_spaces(self):
        """PDF formatting should not split a sentence into separate lines."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "The\n\nEarth   revolves\n around the Sun."
        )

        mock_reader_instance = MagicMock()
        mock_reader_instance.is_encrypted = False
        mock_reader_instance.pages = [mock_page]

        with patch(
            "src.pdf_extractor.PdfReader",
            return_value=mock_reader_instance,
        ):
            result = extract_text_from_pdf(b"mock PDF bytes")

        self.assertEqual(
            result["text"],
            "The Earth revolves around the Sun.",
        )
        self.assertTrue(result["has_text"])
        self.assertEqual(result["page_count"], 1)

    def test_rejects_unsupported_input(self):
        with self.assertRaises(ValueError):
            extract_text_from_pdf(123)

    def test_rejects_invalid_pdf(self):
        with self.assertRaises(ValueError):
            extract_text_from_pdf(b"this is not a PDF")


if __name__ == "__main__":
    unittest.main()
