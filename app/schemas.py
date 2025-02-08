from pydantic import BaseModel
from typing import List, Optional
from app.models.todo import TodoStatus, TodoPriority
from datetime import datetime


class LoginSchema(BaseModel):
    username: str
    password: str


class RegisterSchema(LoginSchema):
    pass


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectResponse(ProjectCreate):
    id: str
    is_owner: bool

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TodoPriority = TodoPriority.MEDIUM
    due_date: Optional[datetime] = None
    project_id: str


class TodoResponse(BaseModel):
    id: str
    title: str
    description: str | None
    status: TodoStatus
    priority: TodoPriority
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None
    user_id: str
    project_id: str

    class Config:
        from_attributes = True


class TodoListResponse(BaseModel):
    todos: List[TodoResponse]


class TodoUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    name: str
    description: str | None = None
