from app.auth.token import get_current_user
from app.database.db import get_db
from app.dependencies.permissions import require_project_member, require_project_owner
from app.models import User
from app.models.project import Project
from app.models.todo import TodoStatus
from app.models.user_notification import UserNotification
from app.models.user_project_sorting import UserProjectSorting
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectSortingResponse,
    ProjectSortingUpdate,
    ProjectStatisticsResponse,
    ProjectUpdate,
    DeleteProjectRequest,
)
from app.utils.project import create_project, get_user_projects, update_project
from app.utils.team_helpers import (
    build_team_members_for_owner,
    build_team_members_for_non_owner,
)
from app.utils.todo_utils import get_project_todos
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pyotp

router = APIRouter()


@router.post("/project", response_model=ProjectResponse)
def create_new_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_project = create_project(db, name=project.name, user_id=current_user.id)
    response_data = {
        "id": new_project.id,
        "name": new_project.name,
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

    my_projects = []
    invited_projects = []
    for project in sorted_projects:
        members = (
            build_team_members_for_owner(project, current_user)
            if project.user_id == current_user.id
            else build_team_members_for_non_owner(project, current_user)
        )
        project_data = {
            "id": project.id,
            "name": project.name,
            "team_members": members,
        }
        if project.user_id == current_user.id:
            my_projects.append(project_data)
        else:
            invited_projects.append(project_data)

    global_unread_count = (
        db.query(UserNotification)
        .filter_by(user_id=current_user.id, read=False)
        .count()
    )
    return ProjectListResponse(
        my_projects=my_projects,
        invited_projects=invited_projects,
        unread_notifications_count=global_unread_count,
    )


@router.get("/project/{project_id}", response_model=ProjectResponse)
def get_project_by_id(
    project: Project = Depends(require_project_member),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    members = (
        build_team_members_for_owner(project, current_user)
        if project.user_id == current_user.id
        else build_team_members_for_non_owner(project, current_user)
    )
    response_data = {
        "id": project.id,
        "name": project.name,
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
    updated_project = update_project(db, project, project_update.name)
    members = build_team_members_for_owner(project, current_user)
    response_data = {
        "id": updated_project.id,
        "name": updated_project.name,
        "team_members": members,
    }
    return response_data


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
    my_projects = []
    invited_projects = []
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
            my_projects.append(project_data)
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
            invited_projects.append(project_data)
    return {"my_projects": my_projects, "invited_projects": invited_projects}


@router.delete("/project/{project_id}")
def delete_project(
    request_body: DeleteProjectRequest,
    project: Project = Depends(require_project_owner),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.twofa_secret:
        if not request_body.totp_code:
            raise HTTPException(
                status_code=400, detail="TOTP code is required for 2FA enabled users"
            )
        totp = pyotp.TOTP(current_user.twofa_secret)
        if not totp.verify(request_body.totp_code):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    from app.models.team import Team
    from app.models.todo import Todo
    from app.models.invite import Invite
    from app.models.notification import Notification
    from app.models.user_notification import UserNotification

    teams = db.query(Team).filter(Team.project_id == project.id).all()
    for team in teams:
        db.delete(team)

    todos = db.query(Todo).filter(Todo.project_id == project.id).all()
    for todo in todos:
        db.delete(todo)

    invites = db.query(Invite).filter(Invite.project_id == project.id).all()
    for invite in invites:
        db.delete(invite)

    notifications = (
        db.query(Notification).filter(Notification.project_id == project.id).all()
    )
    for notif in notifications:
        user_notifs = (
            db.query(UserNotification)
            .filter(UserNotification.notification_id == notif.id)
            .all()
        )
        for un in user_notifs:
            db.delete(un)
        db.delete(notif)

    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}
