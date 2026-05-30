import hashlib
import os
import random

from openai import OpenAI


EMBEDDING_DIMENSION = 1536


def generate_mock_embedding(text: str) -> list[float]:
    """
    Generate a deterministic mock embedding.

    This is not semantic, but it lets the system work when OpenAI quota
    is unavailable. Same text always returns the same vector.
    """
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    seed = int(text_hash[:16], 16)

    random_generator = random.Random(seed)

    return [
        random_generator.uniform(-1.0, 1.0)
        for _ in range(EMBEDDING_DIMENSION)
    ]


def generate_openai_embedding(text: str) -> list[float]:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return generate_mock_embedding(text)

    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    client = OpenAI(api_key=api_key)

    try:
        response = client.embeddings.create(
            model=model,
            input=text,
        )

        return response.data[0].embedding

    except Exception:
        return generate_mock_embedding(text)


def generate_embedding(text: str) -> list[float]:
    use_openai_embeddings = (
        os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
    )

    if use_openai_embeddings:
        return generate_openai_embedding(text)

    return generate_mock_embedding(text)


def get_embedding_status() -> dict:
    use_openai_embeddings = (
        os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
    )
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    if use_openai_embeddings and api_key:
        return {
            "provider": "openai",
            "model": model,
            "enabled": True,
            "api_key_configured": True,
            "dimension": EMBEDDING_DIMENSION,
        }

    if use_openai_embeddings and not api_key:
        return {
            "provider": "mock",
            "model": "mock-embedding",
            "enabled": False,
            "api_key_configured": False,
            "dimension": EMBEDDING_DIMENSION,
            "reason": "USE_OPENAI_EMBEDDINGS is true but OPENAI_API_KEY is missing",
        }

    return {
        "provider": "mock",
        "model": "mock-embedding",
        "enabled": True,
        "api_key_configured": bool(api_key),
        "dimension": EMBEDDING_DIMENSION,
        "reason": "USE_OPENAI_EMBEDDINGS is false",
    }