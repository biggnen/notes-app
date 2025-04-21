from pydantic import BaseModel
from uuid import UUID


class DocumentBase(BaseModel):
    title: str


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    document_id: UUID

    class Config:
        orm_mode = True


class DocumentFullResponse(DocumentResponse):
    content: str | None = None
    plain_text_content: str | None = None


class DocumentContentCreate(BaseModel):
    content: str
    plain_text_content: str | None = None


class DocumentContentResponse(BaseModel):
    content: str
    plain_text_content: str | None = None

    class Config:
        orm_mode = True


class RelationshipCreate(BaseModel):
    target_document_id: UUID
    relationship_type: str = "link"


class AttachmentResponse(BaseModel):
    attachment_id: UUID
    document_id: UUID
    filename: str
    file_type: str
    file_size: int

    class Config:
        orm_mode = True


class AttachmentUploadResponse(BaseModel):
    attachment_id: UUID

    class Config:
        orm_mode = True
