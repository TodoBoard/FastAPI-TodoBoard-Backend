from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
