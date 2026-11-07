"""Extract text from supported RCA source documents."""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".eml"}


def extract_document_text(filename: str, content: bytes) -> str:
    """Extract text from a PDF, plain-text file, or email file."""
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file type '{extension or '(no extension)'}'. "
            f"Supported types: {supported}."
        )

    if not content:
        raise ValueError("The uploaded file is empty.")

    if extension == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))
            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )
        except PdfReadError as exc:
            raise ValueError(
                "The uploaded PDF is invalid or damaged."
            ) from exc
    else:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("cp1252")

    text = text.strip()
    if not text:
        raise ValueError(
            "No text could be extracted from the uploaded file. "
            "Scanned PDFs may need OCR."
        )

    return text