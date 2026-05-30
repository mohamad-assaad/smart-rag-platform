import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.documents.service import get_document_by_id
from app.models import Chunk
from app.rag.chunking import split_text_into_chunks
from app.rag.llm import generate_llm_answer
from app.rag.retrieval import calculate_keyword_score
from app.rag.schemas import (
    AnswerRequest,
    AnswerResponse,
    AnswerSource,
    SearchRequest,
    SearchResult,
    VectorSearchRequest,
    VectorSearchResult,
)
from app.rag.vector_service import search_document_chunks_in_qdrant


SUPPORTED_SEARCH_MODES = {"keyword", "vector", "hybrid"}


def create_chunks_for_document(
    db: Session,
    document_id: UUID,
) -> list[Chunk]:
    document = get_document_by_id(
        db=db,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    existing_chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index.asc())
        .all()
    )

    if existing_chunks:
        return existing_chunks

    text_chunks = split_text_into_chunks(document.content)

    if not text_chunks:
        raise HTTPException(
            status_code=400,
            detail="Document has no content to chunk.",
        )

    created_chunks: list[Chunk] = []

    for index, chunk_text in enumerate(text_chunks):
        chunk = Chunk(
            document_id=document_id,
            chunk_index=index,
            content=chunk_text,
        )

        db.add(chunk)
        created_chunks.append(chunk)

    db.commit()

    for chunk in created_chunks:
        db.refresh(chunk)

    return created_chunks


def get_chunks_by_document(
    db: Session,
    document_id: UUID,
) -> list[Chunk]:
    return (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index.asc())
        .all()
    )


def search_chunks(
    db: Session,
    search_request: SearchRequest,
    top_k: int = 5,
) -> list[SearchResult]:
    document_chunks = get_chunks_by_document(
        db=db,
        document_id=search_request.document_id,
    )

    results: list[SearchResult] = []

    for chunk in document_chunks:
        score = calculate_keyword_score(
            question=search_request.question,
            chunk_content=chunk.content,
        )

        if score > 0:
            results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=score,
                )
            )

    results.sort(key=lambda item: item.score, reverse=True)

    return results[:top_k]


def validate_search_mode(search_mode: str) -> str:
    normalized_search_mode = search_mode.strip().lower()

    if normalized_search_mode not in SUPPORTED_SEARCH_MODES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid search_mode. Supported values are: "
                "keyword, vector, hybrid."
            ),
        )

    return normalized_search_mode


def build_answer_cache_key(answer_request: AnswerRequest) -> str:
    normalized_question = answer_request.question.strip().lower()
    search_mode = validate_search_mode(answer_request.search_mode)

    return (
        f"rag_answer:{search_mode}:"
        f"{answer_request.document_id}:"
        f"{normalized_question}"
    )


def get_cached_answer(cache_key: str) -> AnswerResponse | None:
    try:
        cached_value = redis_client.get(cache_key)

        if cached_value is None:
            return None

        cached_data = json.loads(cached_value)

        return AnswerResponse(**cached_data)

    except Exception:
        # If Redis is down or cache data is invalid, do not break the API.
        return None


def save_answer_to_cache(
    cache_key: str,
    answer_response: AnswerResponse,
    ttl_seconds: int = 300,
) -> None:
    try:
        redis_client.setex(
            cache_key,
            ttl_seconds,
            answer_response.model_dump_json(),
        )
    except Exception:
        # Cache failure should not break the answer endpoint.
        return


def build_answer_from_sources(
    question: str,
    sources: list[AnswerSource],
) -> AnswerResponse:
    if not sources:
        return AnswerResponse(
            question=question,
            answer="I could not find relevant information in the document chunks.",
            sources=[],
        )

    context_chunks = [
        source.content
        for source in sources
    ]

    answer = generate_llm_answer(
        question=question,
        context_chunks=context_chunks,
    )

    return AnswerResponse(
        question=question,
        answer=answer,
        sources=sources,
    )


def get_keyword_sources(
    db: Session,
    answer_request: AnswerRequest,
    limit: int = 5,
) -> list[AnswerSource]:
    search_request = SearchRequest(
        document_id=answer_request.document_id,
        question=answer_request.question,
    )

    keyword_results = search_chunks(
        db=db,
        search_request=search_request,
        top_k=limit,
    )

    return [
        AnswerSource(
            chunk_id=result.chunk_id,
            chunk_index=result.chunk_index,
            score=float(result.score),
            content=result.content,
            source_type="keyword",
        )
        for result in keyword_results
    ]


def get_vector_sources(
    answer_request: AnswerRequest,
    limit: int = 5,
) -> list[AnswerSource]:
    vector_search_request = VectorSearchRequest(
        document_id=answer_request.document_id,
        question=answer_request.question,
        limit=limit,
    )

    try:
        vector_results: list[VectorSearchResult] = search_document_chunks_in_qdrant(
            vector_search_request=vector_search_request,
        )
    except Exception:
        return []

    return [
        AnswerSource(
            chunk_id=result.chunk_id,
            chunk_index=result.chunk_index,
            score=float(result.score),
            content=result.content,
            source_type="vector",
        )
        for result in vector_results
    ]


def normalize_vector_score(score: float) -> float:
    if score < 0:
        return 0.0

    return score


def merge_hybrid_sources(
    keyword_sources: list[AnswerSource],
    vector_sources: list[AnswerSource],
    limit: int = 3,
) -> list[AnswerSource]:
    merged: dict[UUID, AnswerSource] = {}

    for source in keyword_sources:
        merged[source.chunk_id] = AnswerSource(
            chunk_id=source.chunk_id,
            chunk_index=source.chunk_index,
            score=source.score,
            content=source.content,
            source_type="keyword",
        )

    for source in vector_sources:
        vector_score = normalize_vector_score(source.score)

        if source.chunk_id in merged:
            existing_source = merged[source.chunk_id]
            existing_source.score = existing_source.score + vector_score
            existing_source.source_type = "hybrid"
        else:
            merged[source.chunk_id] = AnswerSource(
                chunk_id=source.chunk_id,
                chunk_index=source.chunk_index,
                score=vector_score,
                content=source.content,
                source_type="vector",
            )

    sorted_sources = sorted(
        merged.values(),
        key=lambda source: source.score,
        reverse=True,
    )

    return sorted_sources[:limit]


def generate_answer_from_keyword_search(
    db: Session,
    answer_request: AnswerRequest,
) -> AnswerResponse:
    sources = get_keyword_sources(
        db=db,
        answer_request=answer_request,
        limit=3,
    )

    return build_answer_from_sources(
        question=answer_request.question,
        sources=sources,
    )


def generate_answer_from_vector_search(
    answer_request: AnswerRequest,
) -> AnswerResponse:
    sources = get_vector_sources(
        answer_request=answer_request,
        limit=3,
    )

    if not sources:
        return AnswerResponse(
            question=answer_request.question,
            answer=(
                "I could not find relevant information in the vector store. "
                "Make sure chunks were created and vectors were stored in Qdrant."
            ),
            sources=[],
        )

    return build_answer_from_sources(
        question=answer_request.question,
        sources=sources,
    )


def generate_answer_from_hybrid_search(
    db: Session,
    answer_request: AnswerRequest,
) -> AnswerResponse:
    keyword_sources = get_keyword_sources(
        db=db,
        answer_request=answer_request,
        limit=5,
    )

    vector_sources = get_vector_sources(
        answer_request=answer_request,
        limit=5,
    )

    hybrid_sources = merge_hybrid_sources(
        keyword_sources=keyword_sources,
        vector_sources=vector_sources,
        limit=3,
    )

    return build_answer_from_sources(
        question=answer_request.question,
        sources=hybrid_sources,
    )


def generate_answer(
    db: Session,
    answer_request: AnswerRequest,
) -> AnswerResponse:
    search_mode = validate_search_mode(answer_request.search_mode)

    cache_key = build_answer_cache_key(answer_request)

    cached_answer = get_cached_answer(cache_key)

    if cached_answer is not None:
        cached_answer.answer = "[CACHE HIT] " + cached_answer.answer
        return cached_answer

    if search_mode == "keyword":
        answer_response = generate_answer_from_keyword_search(
            db=db,
            answer_request=answer_request,
        )

    elif search_mode == "vector":
        answer_response = generate_answer_from_vector_search(
            answer_request=answer_request,
        )

    else:
        answer_response = generate_answer_from_hybrid_search(
            db=db,
            answer_request=answer_request,
        )

    save_answer_to_cache(
        cache_key=cache_key,
        answer_response=answer_response,
    )

    return answer_response