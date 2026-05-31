# Smart RAG Platform

A production-style Retrieval-Augmented Generation backend built with FastAPI, PostgreSQL, Redis, Qdrant, Docker Compose, and OpenAI integration.

This project demonstrates a complete backend architecture for a scalable RAG system, including document ingestion, chunking, persistent storage, vector search, hybrid retrieval, caching, API key authentication, file upload support, and LLM-based answer generation with source tracking.

---

## Project Goals

The goal of this project is to build a Smart RAG backend that can:

* Manage customers
* Store customer documents
* Upload `.txt` files as documents
* Split documents into chunks
* Store chunks in PostgreSQL
* Generate embeddings for chunks
* Store vectors in Qdrant
* Search using keyword retrieval
* Search using vector retrieval
* Combine both with hybrid retrieval
* Generate answers using an LLM
* Return answer sources
* Cache repeated answers using Redis
* Protect API endpoints with an API key
* Run the full stack using Docker Compose

---

## Tech Stack

| Layer           | Technology                           |
| --------------- | ------------------------------------ |
| API Backend     | FastAPI                              |
| Database        | PostgreSQL                           |
| ORM             | SQLAlchemy                           |
| Cache           | Redis                                |
| Vector Database | Qdrant                               |
| LLM             | OpenAI API                           |
| Embeddings      | OpenAI Embeddings with mock fallback |
| Authentication  | API Key Header                       |
| File Upload     | FastAPI UploadFile                   |
| Containers      | Docker                               |
| Orchestration   | Docker Compose                       |
| Language        | Python                               |

---

## Architecture

```text
User / Client
    |
    v
FastAPI API
    |
    |---- API Key Authentication
    |
    |---- PostgreSQL
    |       |---- customers
    |       |---- documents
    |       |---- chunks
    |
    |---- Redis
    |       |---- cached RAG answers
    |
    |---- Qdrant
    |       |---- chunk vectors
    |
    |---- OpenAI
            |---- LLM answers
            |---- embeddings
```

---

## RAG Flow

```text
Customer
   |
Document or Uploaded .txt File
   |
Chunking
   |
PostgreSQL chunks
   |
Embeddings
   |
Qdrant vectors
   |
Hybrid Retrieval
   |---- keyword search
   |---- vector search
   |
LLM Answer
   |
Sources
   |
Redis Cache
```

---

## Features

### Customers

* Create customers
* List customers
* Store customers in PostgreSQL
* Protected with API key authentication

### Documents

* Add documents for a customer
* Upload `.txt` files as documents
* List customer documents
* Store documents in PostgreSQL

### Chunking

* Split document content into smaller chunks
* Store chunks in PostgreSQL
* Preserve chunk index and source document

### Retrieval

* Keyword retrieval
* Vector retrieval with Qdrant
* Hybrid retrieval combining keyword and vector results

### LLM Answering

* Generate answers using retrieved context
* Return answer sources
* OpenAI integration
* Mock LLM fallback when OpenAI is unavailable

### Redis Cache

* Cache repeated RAG answers
* Return cached responses for repeated questions
* Cache failures do not break the API

### Authentication

* API key protection using `X-API-Key`
* Protected customer, document, and RAG endpoints
* Clean error response for missing or invalid API keys

### Error Handling

* Validates search mode
* Handles OpenAI failures safely
* Handles Redis failures safely
* Handles missing vector data safely
* Handles invalid file uploads safely

---

## Docker Services

The project runs with Docker Compose and includes:

```text
smart-rag-api        FastAPI backend
smart-rag-postgres   PostgreSQL database
smart-rag-redis      Redis cache
smart-rag-qdrant     Qdrant vector database
```

---

## Environment Variables

Create a `.env` file in the root folder:

```env
OPENAI_API_KEY=your_openai_api_key_here
API_KEY=dev-smart-rag-key
```

The API container uses:

```env
DATABASE_URL=postgresql://rag_user:rag_password@postgres:5432/smart_rag_db
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
USE_OPENAI_LLM=true
USE_OPENAI_EMBEDDINGS=true
API_KEY=dev-smart-rag-key
```

Use `.env.example` as a safe template for GitHub.

Do not commit your real `.env` file.

---

## Authentication

Most API endpoints are protected with an API key.

Required header:

```text
X-API-Key: dev-smart-rag-key
```

Example request:

```powershell
curl.exe -X GET "http://127.0.0.1:8000/customers" -H "X-API-Key: dev-smart-rag-key"
```

Without the API key, protected endpoints return:

```json
{
  "detail": "Invalid or missing API key."
}
```

The API key is configured through the `.env` file:

```env
API_KEY=dev-smart-rag-key
```

---

## Run the Project

From the root folder:

```powershell
docker compose up --build
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## Health Checks

Health endpoints are available for checking the backend and infrastructure services.

### API Health

```text
GET /health
```

### PostgreSQL Health

```text
GET /db/health
```

### Redis Health

```text
GET /cache/health
```

### LLM Health

```text
GET /llm/health
```

### Embeddings Health

```text
GET /embeddings/health
```

### Qdrant Health

```text
GET /vector/health
```

---

## Main API Endpoints

### Customers

```text
POST /customers
GET /customers
```

### Documents

```text
POST /customers/{customer_id}/documents
POST /customers/{customer_id}/documents/upload
GET /customers/{customer_id}/documents
```

The upload endpoint supports `.txt` files.

### Chunks

```text
POST /documents/{document_id}/chunks
GET /documents/{document_id}/chunks
```

### Vectors

```text
POST /documents/{document_id}/vectors
```

### Search

```text
POST /rag/search
POST /rag/vector-search
```

### Answer

```text
POST /rag/answer
```

---

## Example Test Flow

### 1. Create Customer

Endpoint:

```text
POST /customers
```

Header:

```text
X-API-Key: dev-smart-rag-key
```

Body:

```json
{
  "name": "Delta Corp",
  "description": "Customer for RAG testing"
}
```

### 2. Create Document Manually

Endpoint:

```text
POST /customers/{customer_id}/documents
```

Header:

```text
X-API-Key: dev-smart-rag-key
```

Body:

```json
{
  "file_name": "renewal_notes.txt",
  "content": "Delta Corp has a contract renewal coming soon. The customer has reported several support tickets, slow response times, and onboarding documentation issues. The account manager should contact the customer before renewal, review support tickets, and prepare a clear success plan."
}
```

### 3. Create Chunks

Endpoint:

```text
POST /documents/{document_id}/chunks
```

Header:

```text
X-API-Key: dev-smart-rag-key
```

### 4. Store Vectors

Endpoint:

```text
POST /documents/{document_id}/vectors
```

Header:

```text
X-API-Key: dev-smart-rag-key
```

### 5. Ask RAG Answer

Endpoint:

```text
POST /rag/answer
```

Header:

```text
X-API-Key: dev-smart-rag-key
```

Body:

```json
{
  "document_id": "your-document-id",
  "question": "What should the account manager do before the renewal meeting?",
  "search_mode": "hybrid"
}
```

Example response:

```json
{
  "question": "What should the account manager do before the renewal meeting?",
  "answer": "The account manager should contact the customer before renewal, review support tickets, and prepare a clear success plan.",
  "sources": [
    {
      "chunk_id": "example-chunk-id",
      "chunk_index": 1,
      "score": 7.01,
      "content": "account manager should contact the customer before renewal...",
      "source_type": "hybrid"
    }
  ]
}
```

---

## File Upload

The API supports uploading `.txt` files and turning them into documents.

Endpoint:

```text
POST /customers/{customer_id}/documents/upload
```

Required header:

```text
X-API-Key: dev-smart-rag-key
```

Example curl request:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/customers/{customer_id}/documents/upload" -H "X-API-Key: dev-smart-rag-key" -F "file=@test-files/renewal-upload-test.txt;type=text/plain"
```

After uploading a file, the normal RAG flow can be used:

```text
POST /documents/{document_id}/chunks
POST /documents/{document_id}/vectors
POST /rag/answer
```

---

## Search Modes

`POST /rag/answer` supports three search modes:

```text
keyword
vector
hybrid
```

Example:

```json
{
  "document_id": "your-document-id",
  "question": "What are the customer risks?",
  "search_mode": "hybrid"
}
```

Invalid values return a clean error:

```json
{
  "detail": "Invalid search_mode. Supported values are: keyword, vector, hybrid."
}
```

---

## OpenAI Fallback

If OpenAI is unavailable or the account has no quota, the system uses a local mock fallback:

```text
[OPENAI FALLBACK - MOCK USED] OpenAI is currently unavailable, so a local fallback answer was generated.
```

This prevents the API from crashing.

---

## Screenshots

### GitHub Repository

![GitHub Repository](screenshots/github-repo.png)

### Swagger API Endpoints

![Swagger Endpoints](screenshots/swagger-endpoints.png)

### Hybrid RAG Answer

![Hybrid RAG Answer](screenshots/rag-answer.png)

### Qdrant Vector Health

![Vector Health](screenshots/vector-health.png)

---

## Current Status

Implemented:

* FastAPI backend
* PostgreSQL persistence
* SQLAlchemy models
* Redis answer cache
* Qdrant vector database
* OpenAI LLM integration
* Embeddings service
* Mock fallback for LLM and embeddings
* Keyword retrieval
* Vector retrieval
* Hybrid retrieval
* Answer sources
* Docker Compose stack
* Text file upload support
* API key authentication
* Production-style error handling
* Basic backend logging

---

## Future Improvements

Planned improvements:

* User registration and login
* JWT authentication
* PDF parsing
* Background workers for indexing
* LangGraph orchestration
* CI/CD pipeline
* AWS ECS deployment
* Monitoring and logging dashboard
* Frontend dashboard

---

## Author

Built as a portfolio project for AI backend engineering, RAG systems, and production-ready API architecture.
