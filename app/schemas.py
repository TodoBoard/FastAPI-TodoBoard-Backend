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


class TwoFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TwoFARequest(BaseModel):
    totp_code: str


class PasswordResetSchema(BaseModel):
    username: str
    totp_code: str
    new_password: str


class NotificationResponse(BaseModel):
    id: str
    title: str
    description: str | None
    created_at: datetime
    read: bool
    is_global: bool
    project_id: Optional[str] = None

    class Config:
        from_attributes = True


class InviteCreate(BaseModel):
    duration: Optional[str] = None  # e.g. "24h", "7d", "30d", or None for never expire
    max_usage: Optional[int] = None  # positive integer or None for unlimited


class InviteUpdate(BaseModel):
    duration: Optional[str] = None
    max_usage: Optional[int] = None
    active: Optional[bool] = None


class InviteResponse(BaseModel):
    id: str
    project_id: str
    expires_at: Optional[datetime] = None
    max_usage: Optional[int] = None
    usage_count: int
    active: bool

    class Config:
        from_attributes = True
