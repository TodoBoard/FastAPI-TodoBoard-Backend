from datetime import datetime
from typing import Optional
from app.models.todo import TodoPriority, TodoStatus
from pydantic import BaseModel
from pydantic import field_validator


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None
    project_id: str
    assigned_user_id: Optional[str] = None

    @field_validator("priority", mode="before")
    def empty_priority_to_none(cls, v):
        if v == "":
            return None
        return v


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
    assigned_user_id: Optional[str] = None
    assignee_username: Optional[str] = None
    assignee_avatar_id: Optional[int] = None
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
    assignee_username: Optional[str] = None
    assignee_avatar_id: Optional[int] = None
    assigned_user_id: Optional[str] = None
    project_id: str

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
    assigned_user_id: Optional[str] = None

    @field_validator("priority", mode="before")
    def empty_priority_to_none_u(cls, v):
        if v == "":
            return None
        return v
