from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
    ProjectUpdate,
)
from app.utils.project import (
    create_project,
    get_user_projects,
    get_project,
    update_project,
)
from app.auth.token import get_current_user
from app.models import User

router = APIRouter()


@router.post("/project", response_model=ProjectResponse)
def create_new_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_project = create_project(
        db, name=project.name, description=project.description, user_id=current_user.id
    )
    new_project.is_owner = True
    return new_project


@router.get("/projects", response_model=ProjectListResponse)
def list_projects(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    projects = get_user_projects(db, current_user.id)
    for project in projects:
        project.is_owner = project.user_id == current_user.id
    return ProjectListResponse(projects=projects)


@router.get("/project/{project_id}", response_model=ProjectResponse)
def get_project_by_id(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    is_owner = project.user_id == current_user.id
    is_team_member = any(tm.user_id == current_user.id for tm in project.team_members)
    if not (is_owner or is_team_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project",
        )
    project.is_owner = is_owner
    return project


@router.put("/project/{project_id}", response_model=ProjectResponse)
def update_project_endpoint(
    project_id: str,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can update the project",
        )
    updated_project = update_project(
        db, project, project_update.name, project_update.description
    )
    updated_project.is_owner = True
    return updated_project
