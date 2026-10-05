import io
from pathlib import Path

import pymupdf
from docx import Document


def extract_pdf_text(
    file_content: bytes
) -> str:
    """
    Extract text from a PDF file in memory.
    """

    document = pymupdf.open(
        stream=file_content,
        filetype="pdf"
    )

    pages = []

    for page in document:
        text = page.get_text()

        if text.strip():
            pages.append(text)

    document.close()

    return "\n".join(pages)


def extract_docx_text(
    file_content: bytes
) -> str:
    """
    Extract text from a DOCX file in memory.
    """

    document = Document(
        io.BytesIO(file_content)
    )

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(
                paragraph.text
            )

    return "\n".join(paragraphs)


def extract_txt_text(
    file_content: bytes
) -> str:
    """
    Extract text from a TXT file in memory.
    """

    return file_content.decode("utf-8")


def extract_text(
    file_name: str,
    file_content: bytes
) -> str:
    """
    Extract text based on file extension.
    Works entirely in memory — no disk writes.
    """

    extension = (
        Path(file_name).suffix.lower()
    )

    if extension == ".pdf":
        return extract_pdf_text(
            file_content
        )

    if extension == ".docx":
        return extract_docx_text(
            file_content
        )

    if extension == ".txt":
        return extract_txt_text(
            file_content
        )

    raise ValueError(
        f"Unsupported file type: {extension}"
    )