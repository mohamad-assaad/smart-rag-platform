import logging

from fastapi import FastAPI

from app import models
from app.auth_router import router as auth_router
from app.cache import redis_client
from app.customers.router import router as customers_router
from app.database import Base, engine
from app.documents.router import router as documents_router
from app.rag.embeddings import get_embedding_status
from app.rag.llm import get_llm_status
from app.rag.router import router as rag_router
from app.vector_store import qdrant_client


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Smart RAG Platform API",
    description="Backend API for Smart RAG Platform",
    version="0.1.0",
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(documents_router)
app.include_router(rag_router)


@app.get("/")
def home():
    return {"message": "Smart RAG Platform is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db/health")
def database_health_check():
    with engine.connect():
        return {
            "status": "ok",
            "database": "connected",
        }


@app.get("/cache/health")
def cache_health_check():
    redis_client.ping()

    return {
        "status": "ok",
        "cache": "connected",
    }


@app.get("/llm/health")
def llm_health_check():
    return get_llm_status()


@app.get("/vector/health")
def vector_health_check():
    collections = qdrant_client.get_collections()

    return {
        "status": "ok",
        "vector_store": "connected",
        "collections_count": len(collections.collections),
    }


@app.get("/embeddings/health")
def embeddings_health_check():
    return get_embedding_status()