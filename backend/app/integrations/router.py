from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.integrations.dynamics import (
    DynamicsApiError,
    DynamicsConfigError,
    fetch_customer_profiles,
    get_dynamics_status,
)
from app.models import Customer, Document, User


router = APIRouter(prefix="/integrations/dynamics", tags=["Dynamics"])


class DynamicsImportResponse(BaseModel):
    message: str
    customer_id: str
    document_id: str
    file_name: str
    record_count: int
    entity_set_name: str
    table_logical_name: str


@router.get("/status")
async def dynamics_status(current_user: User = Depends(get_current_user)):
    return get_dynamics_status()


@router.get("/customer-profiles")
async def get_customer_profiles(
    limit: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    try:
        return await fetch_customer_profiles(limit=limit)

    except DynamicsConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    except DynamicsApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected Dynamics integration error: {exc}",
        )


@router.post("/import-customer-profiles", response_model=DynamicsImportResponse)
async def import_customer_profiles(
    limit: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Imports Customer Profile records from Dynamics 365 CRM / Dataverse.

    This endpoint:
    1. Fetches records from Dynamics.
    2. Converts them into RAG-ready text.
    3. Creates or reuses a Smart RAG customer called "Dynamics 365 CRM".
    4. Saves the CRM data as a normal Smart RAG document.

    After this endpoint succeeds, the frontend can call:
    POST /documents/{document_id}/chunks
    POST /documents/{document_id}/vectors
    """

    try:
        dynamics_data = await fetch_customer_profiles(limit=limit)

    except DynamicsConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    except DynamicsApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected Dynamics import error: {exc}",
        )

    rag_text = dynamics_data.get("rag_text") or ""
    record_count = dynamics_data.get("record_count", 0)

    if not rag_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Dynamics returned no text to import.",
        )

    dynamics_customer = (
        db.query(Customer)
        .filter(Customer.name == "Dynamics 365 CRM")
        .first()
    )

    if dynamics_customer is None:
        dynamics_customer = Customer(
            name="Dynamics 365 CRM",
            description=(
                "Imported customer profile records from Dynamics 365 CRM / Dataverse."
            ),
        )

        db.add(dynamics_customer)
        db.commit()
        db.refresh(dynamics_customer)

    document = Document(
        customer_id=dynamics_customer.id,
        file_name="dynamics_customer_profiles.txt",
        content=rag_text,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "Dynamics customer profiles imported as a Smart RAG document.",
        "customer_id": str(dynamics_customer.id),
        "document_id": str(document.id),
        "file_name": document.file_name,
        "record_count": record_count,
        "entity_set_name": dynamics_data.get("entity_set_name", ""),
        "table_logical_name": dynamics_data.get("table_logical_name", ""),
    }