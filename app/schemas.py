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
    description: Optional[str] = None


class TeamMemberResponse(BaseModel):
    id: str
    username: str
    avatar_id: int

    class Config:
        from_attributes = True


class ProjectResponse(ProjectCreate):
    id: str
    is_owner: bool
    team_members: List[TeamMemberResponse] = []

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    unread_notifications_count: int


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
    todos: List[TodoResponse]


class TodoUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    name: str
    description: Optional[str] = None


class TwoFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TwoFARequest(BaseModel):
    totp_code: str


# New schema for password reset check endpoint
class PasswordResetCheckSchema(BaseModel):
    username: str


class PasswordResetSchema(BaseModel):
    username: str
    totp_code: str
    new_password: str


class NotificationResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    created_at: datetime
    read: bool
    project_id: Optional[str] = None

    class Config:
        from_attributes = True


class InviteCreate(BaseModel):
    duration: Optional[str] = None
    max_usage: Optional[int] = None


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


class ProjectSortingUpdate(BaseModel):
    project_ids: List[str]


class ProjectSortingResponse(BaseModel):
    project_ids: List[str]
