from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app.documents.schemas import DocumentCreate, DocumentResponse
from app.documents.service import (
    create_document_for_customer,
    get_customer_documents,
)


router = APIRouter(
    tags=["Documents"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "/customers/{customer_id}/documents",
    response_model=DocumentResponse,
)
def create_document_endpoint(
    customer_id: UUID,
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
):
    return create_document_for_customer(
        db=db,
        customer_id=customer_id,
        document_data=document_data,
    )


@router.post(
    "/customers/{customer_id}/documents/upload",
    response_model=DocumentResponse,
)
async def upload_document_endpoint(
    customer_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported right now.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:
        content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 text.",
        )

    document_data = DocumentCreate(
        file_name=file.filename,
        content=content,
    )

    return create_document_for_customer(
        db=db,
        customer_id=customer_id,
        document_data=document_data,
    )


@router.get(
    "/customers/{customer_id}/documents",
    response_model=list[DocumentResponse],
)
def get_customer_documents_endpoint(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    return get_customer_documents(
        db=db,
        customer_id=customer_id,
    )