from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


class UserNotification(Base):
    __tablename__ = "user_notifications"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    notification_id = Column(
        String(36), ForeignKey("notifications.id"), primary_key=True
    )
    read = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="notifications")
    notification = relationship("Notification", back_populates="user_notifications")
