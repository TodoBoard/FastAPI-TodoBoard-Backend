from datetime import datetime
from typing import Optional
from app.models.todo import TodoPriority, TodoStatus
from pydantic import BaseModel


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None
    project_id: str


class TodoResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TodoStatus
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime]
    user_id: str
    project_id: str

    class Config:
        from_attributes = True


class TodoGetResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TodoStatus
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime]
    username: str
    avatar_id: int

    class Config:
        from_attributes = True


class TodoListResponse(BaseModel):
    todos: list[TodoGetResponse]


class TodoUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None
