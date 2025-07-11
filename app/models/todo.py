from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database.db import Base
import enum
from datetime import datetime


class TodoStatus(enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TodoPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Todo(Base):
    __tablename__ = "todos"
    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(
        Enum(TodoStatus, name="todostatus", create_type=False),
        nullable=False,
        default=TodoStatus.TODO,
    )
    priority = Column(Enum(TodoPriority), nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    finished_at = Column(DateTime, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    assigned_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    user = relationship("User", foreign_keys=[user_id], back_populates="todos")
    assignee = relationship("User", foreign_keys=[assigned_user_id], back_populates="assigned_todos")
    project = relationship("Project", back_populates="todos")

    @property
    def assignee_username(self):
        return self.assignee.username if self.assignee else None

    @property
    def assignee_avatar_id(self):
        return self.assignee.avatar_id if self.assignee else None
