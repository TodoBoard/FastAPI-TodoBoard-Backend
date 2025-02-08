from sqlalchemy import Column, String, DateTime, func, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    is_global = Column(Boolean, nullable=False, default=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)

    user_notifications = relationship("UserNotification", back_populates="notification")
    project = relationship("Project", back_populates="notifications")
