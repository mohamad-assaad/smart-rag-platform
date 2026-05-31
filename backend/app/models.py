import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )
    full_name = Column(
        String,
        nullable=True,
    )
    hashed_password = Column(
        String,
        nullable=False,
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class Customer(Base):
    __tablename__ = "customers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name = Column(
        String,
        nullable=False,
    )
    description = Column(
        Text,
        nullable=True,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    documents = relationship(
        "Document",
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    file_name = Column(
        String,
        nullable=False,
    )
    content = Column(
        Text,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    customer = relationship(
        "Customer",
        back_populates="documents",
    )

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(
        Integer,
        nullable=False,
    )
    content = Column(
        Text,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    document = relationship(
        "Document",
        back_populates="chunks",
    )