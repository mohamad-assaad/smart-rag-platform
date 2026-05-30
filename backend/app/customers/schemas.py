from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class CustomerCreate(BaseModel):
    name: str
    description: str | None = None


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True