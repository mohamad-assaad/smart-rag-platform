from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.customers.schemas import CustomerCreate, CustomerResponse
from app.customers.service import create_customer, get_customers
from app.database import get_db
from app.models import User


router = APIRouter(
    tags=["Customers"],
)


@router.post(
    "/customers",
    response_model=CustomerResponse,
)
def create_customer_endpoint(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_customer(
        db=db,
        customer_data=customer_data,
    )


@router.get(
    "/customers",
    response_model=list[CustomerResponse],
)
def get_customers_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_customers(db=db)