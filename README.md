# Smart RAG Platform

Smart RAG Platform is a full-stack AI/RAG application that allows users to upload knowledge documents or import customer profile data from Dynamics 365 CRM, then ask AI-powered questions over the indexed data with source tracking.

The project demonstrates a production-style architecture using a React frontend, FastAPI backend, PostgreSQL, Redis, Qdrant vector database, Docker Compose, JWT authentication, optional OpenAI integration, local fallback AI logic, and Microsoft Dynamics 365 / Dataverse integration.

---

## Key Features

* User authentication with JWT
* Login and registration flow
* Admin dashboard
* Customer management page
* Document management page
* Knowledge document upload
* Dynamics 365 CRM customer profile import
* Dataverse Web API integration
* Microsoft Entra ID App Registration authentication
* RAG-ready document conversion
* Text chunking for uploaded and imported knowledge
* Vector embeddings stored in Qdrant
* AI question answering over indexed knowledge
* Source tracking for AI answers
* Quick Questions / prompt suggestions
* Local fallback AI when OpenAI is unavailable
* Docker Compose development environment
* Production-style separation of backend, frontend, database, cache, and vector store

---

## Screenshots

### Login and Authentication

![Login page](screenshots/01-login.png)

The platform includes a clean login and registration experience backed by JWT authentication.

### Admin Dashboard

![Overview dashboard](screenshots/02-dashboard.png)

The dashboard provides an enterprise-style workspace for managing customer intelligence, uploaded knowledge, Dynamics CRM imports, and AI answer activity.

### Customer Management

![Customers page](screenshots/02-customers.png)

The Customers page demonstrates the admin interface for managing customer records inside the platform.

### Upload Knowledge

![Upload knowledge page](screenshots/04-upload-knowledge.png)

Users can upload knowledge documents, which are processed into chunks and prepared for retrieval.

### Dynamics 365 CRM Integration

![Dynamics page](screenshots/03-dynamics.png)

The Dynamics page connects the platform to Microsoft Dataverse through Microsoft Entra ID authentication and the Dataverse Web API.

### Import from Dynamics

![Dynamics import success](screenshots/04-dynamics-import-success.png)

Dynamics customer profile records are imported, converted into RAG-ready text, chunked, embedded, and stored in Qdrant for semantic search.

### Ask AI with Source Tracking

![AI answer with sources](screenshots/06-ai-answer-sources.png)

The Ask AI page answers questions over indexed documents and imported CRM data while showing the sources used to generate the response.

### GitHub Repository

![GitHub repository](screenshots/07-github-repo.png)

The project is version-controlled with Git and published to GitHub as a portfolio-ready full-stack AI application.

---

## Tech Stack

### Frontend

* React
* TypeScript
* Vite
* CSS
* Enterprise-style admin UI

### Backend

* FastAPI
* Python
* SQLAlchemy
* JWT authentication
* REST API architecture

### Data and Infrastructure

* PostgreSQL
* Redis
* Qdrant vector database
* Docker Compose

### AI and RAG

* Document upload
* Text chunking
* Embeddings
* Vector search
* AI answer generation
* Source tracking
* Optional OpenAI API
* Local fallback answer engine

### CRM Integration

* Dynamics 365 CRM
* Microsoft Dataverse
* Dataverse Web API
* Microsoft Entra ID App Registration
* OAuth client credentials flow

---

## Architecture Overview

The platform follows a full-stack architecture:

```text
React + TypeScript Frontend
        |
        v
FastAPI Backend
        |
        +--> PostgreSQL
        |       Users, customers, documents, chunks
        |
        +--> Redis
        |       Production-style service architecture
        |
        +--> Qdrant
        |       Vector storage and semantic retrieval
        |
        +--> OpenAI or Local Fallback AI
        |       AI answer generation
        |
        +--> Dynamics 365 / Dataverse
                CRM customer profile import
```

---

## RAG Pipeline

The RAG pipeline works as follows:

1. User uploads a knowledge document or imports customer profile data from Dynamics 365 CRM.
2. Backend converts the content into clean RAG-ready text.
3. Text is split into meaningful chunks.
4. Chunks are stored in PostgreSQL.
5. Embeddings are created for each chunk.
6. Vectors are stored in Qdrant.
7. User asks a question in the Ask AI page.
8. Backend retrieves the most relevant chunks from Qdrant.
9. AI generates an answer using the retrieved context.
10. Frontend displays the answer with source tracking.

---

## Dynamics 365 CRM Integration

The platform includes a working Microsoft Dynamics 365 / Dataverse integration.

The integration uses:

* Microsoft Entra ID App Registration
* Tenant ID
* Client ID
* Client Secret
* Power Platform Application User
* Dataverse Web API
* OAuth access token flow

CRM records are imported from a custom table and converted into RAG-ready customer profile text.

### Dynamics Table

```text
Table logical name: new_customerprofile
Entity set name: new_customerprofiles
```

### CRM Fields Used

```text
new_customername
new_email
new_phone
new_country
new_customersegment
new_preferredchannel
new_emailconsent
new_smsconsent
new_lastinteractiondate
new_recentcomplaint
new_interestarea
```

### Dynamics Import Flow

1. Backend authenticates with Microsoft Entra ID.
2. Backend receives an OAuth access token.
3. Backend calls the Dataverse Web API.
4. Customer profile records are retrieved from Dynamics 365.
5. CRM JSON records are converted into readable RAG text.
6. The imported CRM data is saved as:

```text
dynamics_customer_profiles.txt
```

7. The backend chunks the document.
8. Embeddings are created.
9. Vectors are stored in Qdrant.
10. The frontend automatically selects the imported document.
11. The user can ask AI questions over CRM customer data.

---

## Example AI Questions

The platform supports questions such as:

```text
Which customers are from Qatar?
```

Expected answer:

```text
Ahmed Ali and Omar Hassan
```

```text
Which customers gave SMS consent?
```

Expected answer:

```text
Ahmed Ali and Omar Hassan
```

```text
Who has a blocked card complaint?
```

```text
Summarize all Dynamics customer profiles.
```

```text
Which customers are from Syria?
```

```text
Did Khaled give SMS consent?
```

The fallback AI logic also supports country-based questions, specific customer questions, consent questions, complaint questions, and summary-style prompts.

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd smart-rag-platform
```

### 2. Create the environment file

Create a local `.env` file in the project root.

Do not commit this file.

Example:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=smart_rag
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/smart_rag

JWT_SECRET_KEY=change-this-secret

OPENAI_API_KEY=

DYNAMICS_TENANT_ID=
DYNAMICS_CLIENT_ID=
DYNAMICS_CLIENT_SECRET=
DYNAMICS_RESOURCE=https://your-org.crm4.dynamics.com
```

### 3. Start backend services

From the project root:

```bash
docker compose up --build
```

### 4. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev -- --force
```

### 5. Open the application

```text
http://localhost:5173/
```

### 6. Check backend health

```text
http://127.0.0.1:8000/health
```

---

## Docker Services

The local development environment uses Docker Compose for the backend infrastructure.

Typical services include:

* FastAPI backend
* PostgreSQL database
* Redis
* Qdrant vector database

Important Docker files:

```text
docker-compose.yml
docker-compose.prod.yml
frontend/Dockerfile
backend/requirements.txt
```

---

## Environment and Security Notes

Real secrets are stored only in the local root `.env` file.

The `.env` file must not be committed.

Safe environment variable usage in `docker-compose.yml` should look like this:

```yaml
DYNAMICS_TENANT_ID: ${DYNAMICS_TENANT_ID:-}
DYNAMICS_CLIENT_ID: ${DYNAMICS_CLIENT_ID:-}
DYNAMICS_CLIENT_SECRET: ${DYNAMICS_CLIENT_SECRET:-}
```

Security reminders:

* Do not commit `.env`
* Do not commit real client secrets
* Do not commit access tokens
* Do not expose Microsoft Entra secrets in screenshots
* Rotate any secret that was accidentally exposed
* Keep production credentials outside source control

---

## Important Project Files

### Frontend

```text
frontend/src/App.tsx
frontend/src/App.css
frontend/src/index.css
```

### Backend

```text
backend/app/main.py
backend/app/auth.py
backend/app/models.py
backend/app/database.py
backend/app/rag/chunking.py
backend/app/rag/llm.py
backend/app/rag/router.py
backend/app/rag/service.py
backend/app/rag/embeddings.py
backend/app/integrations/dynamics.py
backend/app/integrations/router.py
backend/app/integrations/__init__.py
```

### Docker and Config

```text
docker-compose.yml
docker-compose.prod.yml
frontend/Dockerfile
backend/requirements.txt
```

---

## Backend API Areas

The FastAPI backend includes endpoints for:

* Authentication
* Customers
* Documents
* Uploads
* RAG question answering
* Dynamics CRM import
* Health checks

The backend can be extended with additional enterprise connectors, background jobs, observability, and deployment configuration.

---

## Current Status

Completed:

* Full-stack application structure
* React + TypeScript frontend
* FastAPI backend
* JWT authentication
* PostgreSQL integration
* Redis service
* Qdrant vector database
* Document upload flow
* RAG chunking and retrieval
* AI answer generation
* Source tracking
* Local fallback AI
* Dynamics 365 CRM import
* Dataverse Web API integration
* Enterprise-style admin UI
* Quick Questions for CRM data
* Docker Compose setup
* GitHub-ready screenshots

---

## Future Improvements

Potential next improvements:

* Deploy backend and services to AWS
* Deploy frontend to a static hosting service
* Add CI/CD pipeline
* Add automated tests
* Add role-based access control
* Add background workers for large imports
* Add PDF and DOCX parsing
* Add richer analytics dashboard
* Add multi-tenant workspace support
* Add production monitoring and logging
* Add support for more CRM and enterprise knowledge connectors

---

## Project Purpose

This project was built to demonstrate the ability to design, build, integrate, and ship a complete AI software product.

It combines full-stack development, cloud-ready architecture, enterprise CRM integration, authentication, vector search, retrieval-augmented generation, and practical AI user experience design.

---

## License

This project is for portfolio and educational purposes.
