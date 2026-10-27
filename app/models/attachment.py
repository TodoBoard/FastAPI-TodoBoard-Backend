from sqlalchemy import Column, String, ForeignKey, DateTime, BigInteger, Integer
from sqlalchemy.orm import relationship
from app.database.db import Base
from datetime import datetime


class AttachmentStatus:
    PENDING = "pending"
    UPLOADED = "uploaded"
    DELETED = "deleted"


class TodoAttachment(Base):
    """Every object in the R2 bucket has exactly one row here.

    A row is only removed after its object was deleted from R2, so the sum of
    `size` over all rows is always >= the real bucket size. That sum is what the
    storage quota is checked against.
    """

    __tablename__ = "todo_attachments"
    id = Column(String(36), primary_key=True)
    # SET NULL on todo deletion: the row keeps counting towards the quota until
    # the maintenance job has removed the object from R2.
    todo_id = Column(String(36), ForeignKey("todos.id", ondelete="SET NULL"), nullable=True)
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    object_key = Column(String(255), nullable=False, unique=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(BigInteger, nullable=False)
    status = Column(String(16), nullable=False, default=AttachmentStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    todo = relationship("Todo")
    uploader = relationship("User")

    # Presigned download URL, set by the router before responding.
    url = None
    attachment_count = None

    @property
    def uploader_username(self):
        return self.uploader.username if self.uploader else None


class UploadCounter(Base):
    """Simple counters for rate limits, e.g. `global:2026-10` or `user:<id>:2026-10-27`."""

    __tablename__ = "upload_counters"
    key = Column(String(100), primary_key=True)
    count = Column(Integer, nullable=False, default=0)
