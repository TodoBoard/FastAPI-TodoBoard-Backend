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
    ProjectStatisticsResponse,
)
from app.utils.project import create_project, get_user_projects, update_project
from app.auth.token import get_current_user
from app.models import User
from app.models.team import Team
from app.models.user_project_sorting import UserProjectSorting
from app.dependencies.permissions import require_project_member, require_project_owner
from app.models.project import Project
from app.models.user_notification import UserNotification
from app.utils.notification_utils import (
    create_project_notification,
    create_personal_notification,
)
from app.utils.team_helpers import (
    build_team_members_for_owner,
    build_team_members_for_non_owner,
)
from app.utils.todo_utils import get_project_todos
import uuid
from app.models.todo import TodoStatus

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
    response_data = {
        "id": new_project.id,
        "name": new_project.name,
        "description": new_project.description,
        "is_owner": True,
        "team_members": [
            {
                "id": current_user.id,
                "username": "You",
                "avatar_id": current_user.avatar_id,
            }
        ],
    }
    return response_data


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
                sorted_projects.append(proj)
    for proj in project_dict.values():
        sorted_projects.append(proj)
    project_responses = []
    for project in sorted_projects:
        is_owner = project.user_id == current_user.id
        members = (
            build_team_members_for_owner(project, current_user)
            if is_owner
            else build_team_members_for_non_owner(project, current_user)
        )
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "is_owner": is_owner,
            "team_members": members,
        }
        project_responses.append(project_data)
    global_unread_count = (
        db.query(UserNotification)
        .filter_by(user_id=current_user.id, read=False)
        .count()
    )
    return ProjectListResponse(
        projects=project_responses, unread_notifications_count=global_unread_count
    )


@router.get("/project/{project_id}", response_model=ProjectResponse)
def get_project_by_id(
    project: Project = Depends(require_project_member),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_owner = project.user_id == current_user.id
    members = (
        build_team_members_for_owner(project, current_user)
        if is_owner
        else build_team_members_for_non_owner(project, current_user)
    )
    response_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "is_owner": is_owner,
        "team_members": members,
    }
    return response_data


@router.put("/project/{project_id}", response_model=ProjectResponse)
def update_project_endpoint(
    project_update: ProjectUpdate,
    project: Project = Depends(require_project_owner),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_project = update_project(
        db, project, project_update.name, project_update.description
    )
    members = build_team_members_for_owner(project, current_user)
    response_data = {
        "id": updated_project.id,
        "name": updated_project.name,
        "description": updated_project.description,
        "is_owner": True,
        "team_members": members,
    }
    return response_data


@router.post("/project/{project_id}/leave", response_model=dict)
def leave_project(
    project: Project = Depends(require_project_member),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if project.user_id == current_user.id:
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
    title_global = "User Left Project"
    description_global = (
        f"User {current_user.username} has left the project {project.name}."
    )
    create_project_notification(
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


@router.get("/projects/statistics", response_model=ProjectStatisticsResponse)
def get_project_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    projects = get_user_projects(db, current_user.id)
    own_projects = []
    joined_projects = []
    for project in projects:
        todos = get_project_todos(db, project.id)
        total_tasks = len(todos)
        open_tasks = len([t for t in todos if t.status != TodoStatus.DONE])
        done_tasks = len([t for t in todos if t.status == TodoStatus.DONE])
        percentage = (done_tasks / total_tasks) * 100 if total_tasks > 0 else 0.0

        if project.user_id == current_user.id:
            team_members = build_team_members_for_owner(project, current_user)
            project_data = {
                "id": project.id,
                "name": project.name,
                "team_members": team_members,
                "open_tasks": open_tasks,
                "total_tasks": total_tasks,
                "percentage": percentage,
            }
            own_projects.append(project_data)
        else:
            team_members = build_team_members_for_non_owner(project, current_user)
            project_data = {
                "id": project.id,
                "name": project.name,
                "team_members": team_members,
                "open_tasks": open_tasks,
                "total_tasks": total_tasks,
                "percentage": percentage,
            }
            joined_projects.append(project_data)
    return {"own_projects": own_projects, "joined_projects": joined_projects}
