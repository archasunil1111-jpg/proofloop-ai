
from pathlib import Path
from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf(pdf_file) -> dict:
    """
    Extract and normalize text from a PDF.

    Accepts a file path, bytes, or a file-like object.
    Returns the extracted text and basic document information.
    """

    try:
        if isinstance(pdf_file, (str, Path)):
            reader = PdfReader(str(pdf_file))

        elif isinstance(pdf_file, bytes):
            reader = PdfReader(BytesIO(pdf_file))

        elif hasattr(pdf_file, "read"):
            if hasattr(pdf_file, "seek"):
                pdf_file.seek(0)
            reader = PdfReader(pdf_file)

        else:
            raise ValueError(
                "Provide a PDF path, bytes, or file-like object."
            )

        if reader.is_encrypted:
            raise ValueError(
                "This PDF is encrypted and cannot be read without a password."
            )

        pages_text = []

        for page_number, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""

            # Collapse PDF line breaks and repeated spaces.
            clean_text = " ".join(raw_text.split())

            pages_text.append({
                "page_number": page_number,
                "text": clean_text,
            })

        # Do not add page labels to the evidence text.
        # This helps exact sentence matching work with PDF content.
        full_text = "\n\n".join(
            page["text"]
            for page in pages_text
            if page["text"]
        )

        return {
            "page_count": len(reader.pages),
            "pages": pages_text,
            "text": full_text,
            "has_text": bool(full_text.strip()),
        }

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(
            f"Could not read PDF: {error}"
        ) from error
