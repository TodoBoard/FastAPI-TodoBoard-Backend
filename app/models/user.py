from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    twofa_secret = Column(String(32), nullable=True)
    pending_twofa_secret = Column(String(32), nullable=True)
    projects = relationship("Project", back_populates="user")
    todos = relationship("Todo", back_populates="user")
    notifications = relationship("UserNotification", back_populates="user")
