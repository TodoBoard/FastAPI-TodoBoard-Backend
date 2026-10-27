from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AttachmentCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    size: int


class AttachmentResponse(BaseModel):
    id: str
    todo_id: str
    filename: str
    content_type: str
    size: int
    created_at: datetime
    uploader_username: Optional[str] = None
    url: Optional[str] = None
    # Number of uploaded attachments on the todo, only set on confirm.
    attachment_count: Optional[int] = None

    class Config:
        from_attributes = True


class AttachmentUploadResponse(BaseModel):
    attachment: AttachmentResponse
    upload_url: str
    # Headers the client must send with the PUT, they are part of the signature.
    upload_headers: dict[str, str]


class AttachmentListResponse(BaseModel):
    attachments: list[AttachmentResponse]
