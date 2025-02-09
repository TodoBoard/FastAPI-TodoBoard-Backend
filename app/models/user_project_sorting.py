from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, func
from app.database.db import Base


class UserProjectSorting(Base):
    __tablename__ = "user_project_sorting"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    sorting = Column(JSON, nullable=False)
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
