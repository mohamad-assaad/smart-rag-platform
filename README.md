# Smart RAG Platform

A production-style full-stack AI application for uploading customer knowledge, indexing documents, and generating grounded AI answers with source tracking.

Smart RAG Platform is built as an enterprise customer intelligence workspace. It allows teams to create customer records, upload text knowledge files, split documents into searchable chunks, store embeddings in a vector database, and ask AI-powered questions against indexed content.

The project demonstrates a complete AI software product workflow, including authentication, backend APIs, database persistence, vector search, document processing, frontend dashboard design, Docker-based infrastructure, and production deployment preparation.

---

## Project Goals

The main goal of this project is to demonstrate the ability to build and ship a complete AI software product, not just a small demo.

This project includes:

* A FastAPI backend with protected API routes
* JWT authentication
* PostgreSQL database models
* Customer and document management
* Document upload and chunking
* Vector indexing with Qdrant
* Redis service support
* RAG question answering with source tracking
* OpenAI integration with local fallback behavior
* React + TypeScript frontend
* Professional admin-center user interface
* Docker Compose infrastructure
* Production frontend build support
* Preparation for AWS deployment

---

## Features

### Authentication

* User registration
* User login
* JWT access tokens
* Protected backend routes
* Current user session handling

### Customer Management

* Create customer records
* View customer list
* Store customer descriptions
* Organize uploaded documents by customer

### Document Upload and Indexing

* Upload `.txt` customer knowledge files
* Automatically create document records
* Split uploaded text into clean chunks
* Store chunks for retrieval
* Generate vector embeddings
* Store vectors in Qdrant

### Ask AI

* Ask questions against uploaded customer documents
* Hybrid-style retrieval flow
* AI answer generation
* Source tracking
* Sources hidden by default
* Expandable source chunks
* Local fallback answers when OpenAI is unavailable

### Frontend Admin Dashboard

* Enterprise admin-center layout
* Gray and white professional design
* Left icon rail
* Main navigation panel
* Centered smart search bar
* Search suggestions for pages and content
* Overview, Customers, Documents, Upload Knowledge, and Ask AI pages
* Modern Upload Knowledge interface
* Clean Ask AI answer panel

---

## Tech Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* Redis
* Qdrant
* OpenAI API
* JWT authentication
* Docker

### Frontend

* React
* TypeScript
* Vite
* CSS
* Fetch API
* Local storage token handling

### Infrastructure

* Docker Compose
* PostgreSQL container
* Redis container
* Qdrant container
* FastAPI backend container
* Frontend production Dockerfile with Nginx

---

## Architecture

```text
User
 |
 |  React + TypeScript Frontend
 |  - Login/Register
 |  - Customers
 |  - Document Upload
 |  - Ask AI
 |
 v
FastAPI Backend
 |
 |-- Auth Module
 |   - Register
 |   - Login
 |   - JWT verification
 |
 |-- Customers Module
 |   - Create customers
 |   - List customers
 |
 |-- Documents Module
 |   - Upload text files
 |   - Store document content
 |
 |-- RAG Module
 |   - Chunk documents
 |   - Generate embeddings
 |   - Store vectors in Qdrant
 |   - Retrieve relevant chunks
 |   - Generate AI answers
 |
 |-- PostgreSQL
 |   - Users
 |   - Customers
 |   - Documents
 |   - Chunks
 |
 |-- Redis
 |   - Cache/service support
 |
 |-- Qdrant
 |   - Vector search
 |
 |-- OpenAI
     - Answer generation when API key is available
```

---

## Screenshots

Add screenshots inside the `screenshots` folder.

Recommended screenshot files:

```text
screenshots/frontend-login.png
screenshots/frontend-overview.png
screenshots/frontend-customers.png
screenshots/frontend-upload.png
screenshots/frontend-ask-ai-answer.png
screenshots/frontend-ask-ai-sources.png
```

Example:

```md
![Login Page](screenshots/frontend-login.png)
![Overview Page](screenshots/frontend-overview.png)
![Upload Knowledge](screenshots/frontend-upload.png)
![Ask AI Answer](screenshots/frontend-ask-ai-answer.png)
```

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd smart-rag-platform
```

---

## Backend Setup

The backend runs through Docker Compose.

From the project root:

```bash
docker compose up --build
```

Backend health check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

Open a new terminal and run:

```bash
cd frontend
npm install
npm run dev -- --force
```

Frontend URL:

```text
http://localhost:5173/
```

---

## Frontend Production Build

To verify the frontend production build:

```bash
cd frontend
npm run build
```

Expected successful output:

```text
vite building client environment for production...
built successfully
```

---

## Environment Variables

### Root `.env.example`

Create a `.env` file based on `.env.example`.

```env
# Backend
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/smart_rag
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
JWT_SECRET_KEY=change-this-secret-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Frontend local development
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Frontend `.env.example`

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Do not commit real secrets or API keys.

---

## Main API Flow

### Authentication

1. Register user
2. Login user
3. Store JWT access token
4. Use token for protected requests

### Customer Workflow

1. Create a customer
2. Select customer in the dashboard
3. Upload a `.txt` knowledge document

### RAG Workflow

1. Upload document
2. Create document chunks
3. Generate embeddings
4. Store vectors in Qdrant
5. Ask a question
6. Retrieve relevant chunks
7. Generate an AI answer
8. Show answer with optional sources

---

## Example Test Question

Using the included Mohamad profile test document, ask:

```text
What is the main goal of Mohamad?
```

Expected answer:

```text
Mohamad's main goal is to demonstrate that he can build and ship a complete AI software product, not just a small demo.

Recommendation: finalize the frontend design, take professional screenshots, update the README, dockerize the frontend, prepare production environment variables, and deploy the project on AWS.
```

---

## OpenAI Fallback Behavior

If the OpenAI API key is not configured or the API request fails, the backend uses a local fallback answer generator.

This keeps the product usable during local development and portfolio demonstrations.

The fallback system is especially useful for:

* Testing the full RAG flow
* Avoiding broken demos when OpenAI is unavailable
* Showing a working AI answer interface without requiring a live API key

---

## Docker Services

The local Docker Compose setup includes:

```text
postgres
redis
qdrant
backend api
```

The frontend also includes a production Dockerfile using:

```text
Node.js build stage
Nginx serving stage
```

---

## Frontend Dockerfile

The frontend Dockerfile builds the React application and serves the static production files with Nginx.

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## Production Deployment Plan

Recommended first production deployment:

```text
AWS EC2 + Docker Compose
```

Production services:

* Frontend container
* Backend container
* PostgreSQL container
* Redis container
* Qdrant container

Future improvements:

* Nginx reverse proxy
* HTTPS with Certbot
* Domain name
* Managed PostgreSQL with Amazon RDS
* Managed Redis with ElastiCache
* Persistent Qdrant storage
* CI/CD with GitHub Actions
* CloudWatch logging
* S3 document storage

---

## AWS Deployment Preparation

Before deploying to AWS:

* Verify `docker compose up --build` works locally
* Confirm backend health endpoint works
* Confirm frontend production build works
* Confirm login works
* Confirm customer creation works
* Confirm upload and indexing works
* Confirm Ask AI works
* Confirm sources are hidden by default
* Confirm screenshots are updated
* Confirm README is complete
* Confirm real secrets are not committed

---

## Current Status

Completed:

* Backend API
* Authentication
* Customer management
* Document upload
* Chunking
* Vector indexing
* Ask AI flow
* Source tracking
* Local fallback answers
* Professional frontend dashboard
* Frontend production build
* Frontend Dockerfile
* Screenshots folder

Next steps:

* Finalize README
* Add production Docker Compose configuration
* Prepare AWS EC2 deployment
* Add Nginx reverse proxy
* Add HTTPS
* Deploy live version

---

## Author

Built by Mohamad Ali Assaad as a production-style AI portfolio project.

This project demonstrates full-stack engineering, AI integration, backend architecture, frontend product design, Docker infrastructure, and cloud deployment readiness.
