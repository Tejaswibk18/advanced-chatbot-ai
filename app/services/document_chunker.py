def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[str]:
    """
    Split document text into overlapping chunks.

    Args:
        text: Complete document text.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters.

    Returns:
        List of text chunks.
    """

    if not text.strip():
        return []

    text = text.strip()

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks