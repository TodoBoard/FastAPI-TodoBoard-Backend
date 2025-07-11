from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.database.db import Base
from app.models.todo import Todo


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    twofa_secret = Column(String(32), nullable=True)
    pending_twofa_secret = Column(String(32), nullable=True)
    avatar_id = Column(Integer, nullable=False)

    projects = relationship("Project", back_populates="user")
    todos = relationship("Todo", foreign_keys=[Todo.user_id], back_populates="user")
    assigned_todos = relationship("Todo", foreign_keys="Todo.assigned_user_id", back_populates="assignee")
    notifications = relationship("UserNotification", back_populates="user")
