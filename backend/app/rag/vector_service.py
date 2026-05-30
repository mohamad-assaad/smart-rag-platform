from uuid import UUID

from fastapi import HTTPException
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sqlalchemy.orm import Session

from app.models import Chunk
from app.rag.embeddings import EMBEDDING_DIMENSION, generate_embedding
from app.rag.schemas import VectorSearchRequest, VectorSearchResult
from app.vector_store import qdrant_client


COLLECTION_NAME = "document_chunks"


def ensure_chunks_collection_exists() -> None:
    collections = qdrant_client.get_collections().collections
    collection_names = [collection.name for collection in collections]

    if COLLECTION_NAME in collection_names:
        return

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=Distance.COSINE,
        ),
    )


def store_document_chunks_in_qdrant(
    db: Session,
    document_id: UUID,
) -> dict:
    ensure_chunks_collection_exists()

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index.asc())
        .all()
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No chunks found for this document. Create chunks first.",
        )

    points: list[PointStruct] = []

    for chunk in chunks:
        embedding = generate_embedding(chunk.content)

        point = PointStruct(
            id=str(chunk.id),
            vector=embedding,
            payload={
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
            },
        )

        points.append(point)

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return {
        "status": "ok",
        "collection": COLLECTION_NAME,
        "document_id": str(document_id),
        "vectors_stored": len(points),
    }


def search_document_chunks_in_qdrant(
    vector_search_request: VectorSearchRequest,
) -> list[VectorSearchResult]:
    ensure_chunks_collection_exists()

    query_embedding = generate_embedding(vector_search_request.question)

    search_filter = Filter(
        must=[
            FieldCondition(
                key="document_id",
                match=MatchValue(
                    value=str(vector_search_request.document_id),
                ),
            )
        ]
    )

    query_response = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=search_filter,
        limit=vector_search_request.limit,
    )

    results: list[VectorSearchResult] = []

    for point in query_response.points:
        payload = point.payload or {}

        results.append(
            VectorSearchResult(
                chunk_id=UUID(str(payload["chunk_id"])),
                document_id=UUID(str(payload["document_id"])),
                chunk_index=int(payload["chunk_index"]),
                content=str(payload["content"]),
                score=float(point.score),
            )
        )

    return results