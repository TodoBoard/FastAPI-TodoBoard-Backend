from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.todo import TodoStatus, TodoPriority


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TodoPriority = TodoPriority.MEDIUM
    due_date: Optional[datetime] = None
    project_id: str


class TodoResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TodoStatus
    priority: TodoPriority
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime]
    user_id: str
    project_id: str

    class Config:
        from_attributes = True


class TodoListResponse(BaseModel):
    todos: list[TodoResponse]


class TodoUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None
