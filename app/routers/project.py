from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
    ProjectUpdate,
    ProjectSortingUpdate,
    ProjectSortingResponse,
)
from app.utils.project import (
    create_project,
    get_user_projects,
    update_project,
)
from app.auth.token import get_current_user
from app.models import User
from app.models.team import Team
from app.models.user_project_sorting import UserProjectSorting
from app.dependencies.permissions import require_project_member, require_project_owner
from app.models.project import Project

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
    project_dict = {project.id: project for project in projects}

    sorting_record = (
        db.query(UserProjectSorting)
        .filter(UserProjectSorting.user_id == current_user.id)
        .first()
    )

    sorted_projects = []
    if sorting_record:
        for proj_id in sorting_record.sorting:
            if proj_id in project_dict:
                proj = project_dict.pop(proj_id)
                proj.is_owner = proj.user_id == current_user.id
                sorted_projects.append(proj)
    for proj in project_dict.values():
        proj.is_owner = proj.user_id == current_user.id
        sorted_projects.append(proj)

    return ProjectListResponse(projects=sorted_projects)


@router.get("/project/{project_id}", response_model=ProjectResponse)
def get_project_by_id(project: Project = Depends(require_project_member)):
    return project


@router.put("/project/{project_id}", response_model=ProjectResponse)
def update_project_endpoint(
    project_update: ProjectUpdate,
    project: Project = Depends(require_project_owner),
    db: Session = Depends(get_db),
):
    updated_project = update_project(
        db, project, project_update.name, project_update.description
    )
    updated_project.is_owner = True
    return updated_project


@router.post("/project/{project_id}/leave", response_model=dict)
def leave_project(
    project: Project = Depends(require_project_member),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if project.is_owner:
        raise HTTPException(
            status_code=400, detail="Project owner cannot leave the project"
        )

    team_member = (
        db.query(Team)
        .filter(Team.project_id == project.id, Team.user_id == current_user.id)
        .first()
    )
    if not team_member:
        raise HTTPException(
            status_code=400, detail="User is not a member of the project"
        )
    db.delete(team_member)
    db.commit()

    from app.utils.notification_utils import (
        create_global_notification,
        create_personal_notification,
    )

    title_global = "User Left Project"
    description_global = (
        f"User {current_user.username} has left the project {project.name}."
    )
    create_global_notification(
        db, title=title_global, description=description_global, project_id=project.id
    )

    title_personal = "Left Project Confirmation"
    description_personal = f"You have successfully left the project {project.name}."
    create_personal_notification(
        db,
        user_id=current_user.id,
        title=title_personal,
        description=description_personal,
    )

    return {"message": "Left project successfully"}


@router.put("/projects/sort", response_model=ProjectSortingResponse)
def update_project_sorting(
    sorting_update: ProjectSortingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sorting_record = (
        db.query(UserProjectSorting)
        .filter(UserProjectSorting.user_id == current_user.id)
        .first()
    )
    if sorting_record:
        sorting_record.sorting = sorting_update.project_ids
    else:
        sorting_record = UserProjectSorting(
            user_id=current_user.id, sorting=sorting_update.project_ids
        )
        db.add(sorting_record)
    db.commit()
    db.refresh(sorting_record)
    return ProjectSortingResponse(project_ids=sorting_record.sorting)
