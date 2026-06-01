import re


DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 120


def clean_text(text: str) -> str:
    """
    Cleans text but keeps enough structure for RAG.
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _looks_like_dynamics_customer_profiles(text: str) -> bool:
    """
    Detects imported Dynamics CRM customer profile text.
    """
    lowered = text.lower()

    return (
        "customer profile" in lowered
        and "customer name:" in lowered
        and "recent complaint:" in lowered
    )


def _split_dynamics_customer_profiles(text: str) -> list[str]:
    """
    Keeps each Dynamics Customer Profile as its own chunk.

    This prevents answers from missing records because a customer profile was
    cut in the middle by generic character chunking.
    """
    cleaned = clean_text(text)

    pattern = re.compile(
        r"(Customer Profile\s+\d+.*?)(?=\n\n---\n\nCustomer Profile\s+\d+|$)",
        re.IGNORECASE | re.DOTALL,
    )

    matches = pattern.findall(cleaned)

    chunks: list[str] = []

    for match in matches:
        chunk = match.replace("\n\n---", "").strip()
        chunk = re.sub(r"\s+", " ", chunk)

        if chunk:
            chunks.append(chunk)

    if chunks:
        return chunks

    # Fallback if separators were flattened.
    fallback_pattern = re.compile(
        r"(Customer Profile\s+\d+.*?)(?=Customer Profile\s+\d+|$)",
        re.IGNORECASE | re.DOTALL,
    )

    fallback_matches = fallback_pattern.findall(cleaned)

    for match in fallback_matches:
        chunk = re.sub(r"\s+", " ", match).strip()

        if chunk:
            chunks.append(chunk)

    return chunks


def _split_long_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Generic chunking for normal uploaded documents.
    """
    cleaned = clean_text(text)

    if not cleaned:
        return []

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    text_length = len(cleaned)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            sentence_break = cleaned.rfind(".", start, end)
            newline_break = cleaned.rfind("\n", start, end)
            space_break = cleaned.rfind(" ", start, end)

            best_break = max(sentence_break, newline_break, space_break)

            if best_break > start + int(chunk_size * 0.55):
                end = best_break + 1

        chunk = cleaned[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(0, end - chunk_overlap)

    return chunks


def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Main chunking function used by the RAG pipeline.

    For Dynamics CRM imports:
    - one Customer Profile = one chunk

    For normal uploaded documents:
    - use generic character-based chunking with overlap
    """
    cleaned = clean_text(text)

    if not cleaned:
        return []

    if _looks_like_dynamics_customer_profiles(cleaned):
        dynamics_chunks = _split_dynamics_customer_profiles(cleaned)

        if dynamics_chunks:
            return dynamics_chunks

    return _split_long_text(
        cleaned,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def split_text(text: str) -> list[str]:
    """
    Compatibility alias.
    """
    return split_text_into_chunks(text)


def chunk_text(text: str) -> list[str]:
    """
    Compatibility alias.
    """
    return split_text_into_chunks(text)