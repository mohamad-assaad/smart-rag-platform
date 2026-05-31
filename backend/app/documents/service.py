from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.customers.service import get_customer_by_id
from app.documents.schemas import DocumentCreate
from app.models import Document


def create_document_for_customer(
    db: Session,
    customer_id: UUID,
    document_data: DocumentCreate,
) -> Document:
    customer = get_customer_by_id(
        db=db,
        customer_id=customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    document = Document(
        customer_id=customer_id,
        file_name=document_data.file_name,
        content=document_data.content,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_customer_documents(
    db: Session,
    customer_id: UUID,
) -> list[Document]:
    customer = get_customer_by_id(
        db=db,
        customer_id=customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return (
        db.query(Document)
        .filter(Document.customer_id == customer_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def get_document_by_id(
    db: Session,
    document_id: UUID,
) -> Document | None:
    return (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )