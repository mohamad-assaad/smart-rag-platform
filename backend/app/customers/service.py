from sqlalchemy.orm import Session

from app.customers.schemas import CustomerCreate
from app.models import Customer


def create_customer(
    db: Session,
    customer_data: CustomerCreate,
) -> Customer:
    customer = Customer(
        name=customer_data.name,
        description=customer_data.description,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customers(db: Session) -> list[Customer]:
    return db.query(Customer).order_by(Customer.created_at.desc()).all()