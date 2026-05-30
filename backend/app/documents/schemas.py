from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class DocumentCreate(BaseModel):
    file_name: str
    content: str


class DocumentResponse(BaseModel):
    id: UUID
    customer_id: UUID
    file_name: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True