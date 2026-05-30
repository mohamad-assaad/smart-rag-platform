from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    document_id: UUID
    question: str


class SearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    score: int


class VectorSearchRequest(BaseModel):
    document_id: UUID
    question: str
    limit: int = 5


class VectorSearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    score: float


class AnswerRequest(BaseModel):
    document_id: UUID
    question: str
    search_mode: str = "hybrid"


class AnswerSource(BaseModel):
    chunk_id: UUID
    chunk_index: int
    score: float
    content: str
    source_type: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list[AnswerSource]