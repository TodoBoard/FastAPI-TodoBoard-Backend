from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database.db import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    user_notifications = relationship("UserNotification", back_populates="notification")
