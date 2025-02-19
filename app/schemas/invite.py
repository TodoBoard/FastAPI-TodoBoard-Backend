from datetime import datetime
from pydantic import BaseModel
from typing import Optional


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
    project_name: str
    invite_creator_username: str
    invite_creator_avatar_id: int

    class Config:
        from_attributes = True
