from typing import List
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    team_members: List[dict] = []

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    my_projects: List[ProjectResponse]
    invited_projects: List[ProjectResponse]
    unread_notifications_count: int


class ProjectUpdate(BaseModel):
    name: str


class ProjectSortingUpdate(BaseModel):
    project_ids: List[str]


class ProjectSortingResponse(BaseModel):
    project_ids: List[str]


class ProjectStatistic(BaseModel):
    id: str
    name: str
    team_members: List[dict]
    open_tasks: int
    total_tasks: int
    percentage: float

    class Config:
        from_attributes = True


class ProjectStatisticsResponse(BaseModel):
    my_projects: List[ProjectStatistic]
    invited_projects: List[ProjectStatistic]
