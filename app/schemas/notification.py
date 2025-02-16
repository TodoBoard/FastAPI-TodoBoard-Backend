from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    created_at: datetime
    read: bool
    project_id: Optional[str] = None

    class Config:
        from_attributes = True
