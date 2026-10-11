
from pathlib import Path
from io import BytesIO

from pypdf import PdfReader
import pypdfium2 as pdfium
import pytesseract


# Configure Tesseract automatically on Windows when installed
DEFAULT_TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

if DEFAULT_TESSERACT_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(
        DEFAULT_TESSERACT_PATH
    )


def extract_text_from_pdf(pdf_file) -> dict:
    """
    Extract and normalize text from a PDF.

    Supports:
    - PDF file paths
    - PDF bytes
    - File-like objects

    Uses OCR for pages without selectable text.

    Returns page count, individual page text, full text,
    and whether any text was extracted.
    """

    try:
        # Convert supported inputs into PDF bytes.
        if isinstance(pdf_file, (str, Path)):
            pdf_bytes = Path(pdf_file).read_bytes()

        elif isinstance(pdf_file, bytes):
            pdf_bytes = pdf_file

        elif hasattr(pdf_file, "read"):
            if hasattr(pdf_file, "seek"):
                pdf_file.seek(0)

            pdf_bytes = pdf_file.read()

            if isinstance(pdf_bytes, str):
                raise ValueError(
                    "The PDF file must be opened in binary mode."
                )

        else:
            raise ValueError(
                "Provide a PDF path, bytes, or file-like object."
            )

        reader = PdfReader(BytesIO(pdf_bytes))

        if reader.is_encrypted:
            raise ValueError(
                "This PDF is encrypted and cannot be read "
                "without a password."
            )

        pages_text = []
        pdfium_document = None

        try:
            for page_index, page in enumerate(
                reader.pages
            ):
                raw_text = page.extract_text() or ""

                # Normalize line breaks and repeated whitespace.
                clean_text = " ".join(raw_text.split())

                # Use OCR only if the page has no selectable text.
                if not clean_text:
                    if pdfium_document is None:
                        pdfium_document = pdfium.PdfDocument(
                            pdf_bytes
                        )

                    rendered_page = pdfium_document[
                        page_index
                    ]

                    bitmap = rendered_page.render(
                        scale=2
                    )

                    try:
                        image = bitmap.to_pil()

                        raw_text = (
                            pytesseract.image_to_string(
                                image,
                                lang="eng"
                            )
                        )

                    finally:
                        bitmap.close()
                        rendered_page.close()

                    # Normalize OCR output as well.
                    clean_text = " ".join(raw_text.split())

                pages_text.append({
                    "page_number": page_index + 1,
                    "text": clean_text,
                })

        finally:
            if pdfium_document is not None:
                pdfium_document.close()

        # Avoid adding artificial page labels to evidence text.
        full_text = "\n\n".join(
            page["text"]
            for page in pages_text
            if page["text"]
        )

        return {
            "page_count": len(pages_text),
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
