from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
from uuid import UUID
from db import SessionLocal, engine, Base
from models import (
    Document,
    DocumentContent,
    DocumentRelationship,
    Attachment,
    AttachmentContent,
)
from schemas import *
import uuid
import socket

from consul import Consul

app = FastAPI()


async def get_db():
    async with SessionLocal() as session:
        yield session


@app.on_event("startup")
async def on_startup():
    # Register service with Consul
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    consul = Consul(host="consul", port=8500)  # Consul service address
    service_name = "notes-api"
    port = 8000
    ip = socket.gethostbyname(socket.gethostname())
    sid = f"{service_name}-{str(uuid.uuid4())[:8]}"

    # Register the service
    consul.agent.service.register(
        service_name,
        service_id=sid,
        port=port,
        tags=["fastapi", "api", "notes"],
        address=ip,
        check={
            "http": f"http://{ip}:{port}/health",
            "interval": "10s",
        },
    )


@app.on_event("shutdown")
async def on_shutdown():
    consul = Consul(host="consul", port=8500)
    consul.agent.service.deregister("notes-api")
    print("Service deregistered from Consul")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents/", response_model=DocumentResponse)
async def create_document(doc: DocumentCreate, db: AsyncSession = Depends(get_db)):
    new_doc = Document(title=doc.title)
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    return new_doc


@app.get("/documents/{doc_id}", response_model=DocumentFullResponse)
async def get_document(doc_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.document_id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await db.execute(
        select(DocumentContent).where(DocumentContent.document_id == doc_id)
    )
    content = result.scalar_one_or_none()

    return DocumentFullResponse(
        document_id=document.document_id,
        title=document.title,
        content=content.content if content else None,
        plain_text_content=content.plain_text_content if content else None,
    )


@app.put("/documents/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: UUID, update_data: DocumentUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.document_id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.title = update_data.title
    await db.commit()
    await db.refresh(document)
    return document


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Document).where(Document.document_id == doc_id))
    await db.commit()
    return {"detail": "Document deleted"}


@app.post("/documents/{doc_id}/content")
async def set_document_content(
    doc_id: UUID, content: DocumentContentCreate, db: AsyncSession = Depends(get_db)
):
    doc_content = DocumentContent(
        document_id=doc_id,
        content=content.content,
        plain_text_content=content.plain_text_content,
    )
    db.merge(doc_content)
    await db.commit()
    return {"detail": "Content updated"}


@app.post("/documents/{doc_id}/relationships")
async def add_relationship(
    doc_id: UUID, rel: RelationshipCreate, db: AsyncSession = Depends(get_db)
):
    new_rel = DocumentRelationship(
        source_document_id=doc_id,
        target_document_id=rel.target_document_id,
        relationship_type=rel.relationship_type,
    )
    db.add(new_rel)
    await db.commit()
    return {"detail": "Relationship added"}


@app.post("/documents/{doc_id}/attachments")
async def upload_attachment(
    doc_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    attach_id = uuid.uuid4()

    metadata = Attachment(
        attachment_id=attach_id,
        document_id=doc_id,
        filename=file.filename,
        file_type=file.content_type,
        file_size=len(content),
    )
    db.add(metadata)

    bin_data = AttachmentContent(attachment_id=attach_id, content=content)
    db.add(bin_data)

    await db.commit()
    return {"attachment_id": attach_id}


@app.get("/documents/{doc_id}/attachments")
async def list_attachments(doc_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Attachment).where(Attachment.document_id == doc_id)
    )
    attachments = result.scalars().all()
    return attachments
