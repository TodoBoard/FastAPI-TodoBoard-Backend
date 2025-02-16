from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class NotificationResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    created_at: datetime
    read: bool
    project_id: Optional[str] = None

    class Config:
        from_attributes = True
