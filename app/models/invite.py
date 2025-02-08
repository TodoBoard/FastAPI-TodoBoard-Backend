from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.db import Base


class Invite(Base):
    __tablename__ = "invites"
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    max_usage = Column(Integer, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)

    project = relationship("Project", back_populates="invites")
