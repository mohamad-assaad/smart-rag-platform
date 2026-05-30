from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.documents.schemas import DocumentCreate, DocumentResponse
from app.documents.service import create_document, get_documents_by_customer


router = APIRouter(
    prefix="/customers/{customer_id}/documents",
    tags=["Documents"],
)


@router.post("", response_model=DocumentResponse)
def create_document_endpoint(
    customer_id: UUID,
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
):
    return create_document(
        db=db,
        customer_id=customer_id,
        document_data=document_data,
    )


@router.get("", response_model=list[DocumentResponse])
def get_customer_documents_endpoint(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    return get_documents_by_customer(
        db=db,
        customer_id=customer_id,
    )