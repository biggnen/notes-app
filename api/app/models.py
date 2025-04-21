from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from db import Base


class Document(Base):
    __tablename__ = "documents"
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DocumentContent(Base):
    __tablename__ = "document_content"
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        primary_key=True,
    )
    content = Column(Text)
    plain_text_content = Column(Text)


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"
    relationship_id = Column(Integer, primary_key=True, autoincrement=True)
    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE")
    )
    target_document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE")
    )
    relationship_type = Column(String(50), default="link")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Attachment(Base):
    __tablename__ = "attachments"
    attachment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE")
    )
    filename = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class AttachmentContent(Base):
    __tablename__ = "attachment_content"
    attachment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attachments.attachment_id", ondelete="CASCADE"),
        primary_key=True,
    )
    content = Column(Text)
