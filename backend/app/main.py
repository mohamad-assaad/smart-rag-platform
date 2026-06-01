from pydantic import BaseModel
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models
from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.customers.router import router as customers_router
from app.database import engine, get_db
from app.documents.router import router as documents_router
from app.integrations.router import router as integrations_router
from app.models import User
from app.rag.router import router as rag_router


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart RAG Platform",
    description="Customer intelligence platform with document upload, RAG answers, source tracking, and Dynamics 365 integration.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


def serialize_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@app.post("/auth/register")
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()

    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    if not payload.password:
        raise HTTPException(status_code=400, detail="Password is required.")

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered.",
        )

    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return serialize_user(user)


@app.post("/auth/login")
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled.",
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)


app.include_router(customers_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(integrations_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "smart-rag-api",
        "features": {
            "auth": True,
            "customers": True,
            "documents": True,
            "rag": True,
            "dynamics_integration": True,
        },
    }


@app.get("/")
def root():
    return {
        "message": "Smart RAG Platform API",
        "docs": "/docs",
        "health": "/health",
    }