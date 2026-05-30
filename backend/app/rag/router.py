from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.rag.schemas import (
    AnswerRequest,
    AnswerResponse,
    ChunkResponse,
    SearchRequest,
    SearchResult,
    VectorSearchRequest,
    VectorSearchResult,
)
from app.rag.service import (
    create_chunks_for_document,
    generate_answer,
    get_chunks_by_document,
    search_chunks,
)
from app.rag.vector_service import (
    search_document_chunks_in_qdrant,
    store_document_chunks_in_qdrant,
)


router = APIRouter(
    tags=["RAG"],
)


@router.post(
    "/documents/{document_id}/chunks",
    response_model=list[ChunkResponse],
)
def create_chunks_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    return create_chunks_for_document(
        db=db,
        document_id=document_id,
    )


@router.get(
    "/documents/{document_id}/chunks",
    response_model=list[ChunkResponse],
)
def get_chunks_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    return get_chunks_by_document(
        db=db,
        document_id=document_id,
    )


@router.post(
    "/documents/{document_id}/vectors",
)
def store_vectors_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    return store_document_chunks_in_qdrant(
        db=db,
        document_id=document_id,
    )


@router.post(
    "/rag/search",
    response_model=list[SearchResult],
)
def search_chunks_endpoint(
    search_request: SearchRequest,
    db: Session = Depends(get_db),
):
    return search_chunks(
        db=db,
        search_request=search_request,
    )


@router.post(
    "/rag/vector-search",
    response_model=list[VectorSearchResult],
)
def vector_search_chunks_endpoint(
    vector_search_request: VectorSearchRequest,
):
    return search_document_chunks_in_qdrant(
        vector_search_request=vector_search_request,
    )


@router.post(
    "/rag/answer",
    response_model=AnswerResponse,
)
def answer_question_endpoint(
    answer_request: AnswerRequest,
    db: Session = Depends(get_db),
):
    return generate_answer(
        db=db,
        answer_request=answer_request,
    )