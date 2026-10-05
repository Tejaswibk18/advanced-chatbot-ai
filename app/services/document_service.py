import os
from pathlib import Path

import pymupdf 
from docx import Document


# Use DATA_DIR env variable if set (e.g. Render persistent disk at /data),
# otherwise fall back to the project root for local development.
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[2]))

DOCUMENTS_DIR = DATA_DIR / "documents"

DOCUMENTS_DIR.mkdir(
    exist_ok=True
)


def save_document(
    file_name: str,
    file_content: bytes
) -> Path:
    """
    Save an uploaded document locally.
    """

    file_path = DOCUMENTS_DIR / file_name

    file_path.write_bytes(
        file_content
    )

    return file_path


def extract_pdf_text(
    file_path: Path
) -> str:
    """
    Extract text from a PDF file.
    """

    document = pymupdf.open(
        file_path
    )

    pages = []

    for page in document:
        text = page.get_text()

        if text.strip():
            pages.append(text)

    document.close()

    return "\n".join(pages)


def extract_docx_text(
    file_path: Path
) -> str:
    """
    Extract text from a DOCX file.
    """

    document = Document(
        file_path
    )

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(
                paragraph.text
            )

    return "\n".join(paragraphs)


def extract_txt_text(
    file_path: Path
) -> str:
    """
    Extract text from a TXT file.
    """

    return file_path.read_text(
        encoding="utf-8"
    )


def extract_text(
    file_path: Path
) -> str:
    """
    Extract text based on
    document extension.
    """

    extension = (
        file_path.suffix.lower()
    )

    if extension == ".pdf":
        return extract_pdf_text(
            file_path
        )

    if extension == ".docx":
        return extract_docx_text(
            file_path
        )

    if extension == ".txt":
        return extract_txt_text(
            file_path
        )

    raise ValueError(
        f"Unsupported file type: {extension}"
    )