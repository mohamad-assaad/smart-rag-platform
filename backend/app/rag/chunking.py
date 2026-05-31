def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 80,
) -> list[str]:
    """
    Split text into clean chunks without cutting words in half.

    This keeps Ask AI source snippets readable by avoiding broken starts like
    "isual noise" or "anager should".
    """
    clean_text = " ".join(text.split())

    if not clean_text:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(clean_text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        # Move the chunk end back to the nearest space.
        if end < text_length:
            last_space = clean_text.rfind(" ", start, end)

            if last_space != -1 and last_space > start:
                end = last_space

        chunk = clean_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        # Keep overlap, but move next chunk start to the next word boundary.
        next_start = max(0, end - overlap)

        if next_start > 0:
            next_space = clean_text.find(" ", next_start)

            if next_space != -1:
                next_start = next_space + 1

        # Safety guard against infinite loops.
        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


# Backward-compatible alias in case another file imports chunk_text.
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    return split_text_into_chunks(text, chunk_size, overlap)