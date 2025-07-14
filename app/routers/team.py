from app.auth.token import get_current_user
from app.database.db import get_db
from app.dependencies.permissions import require_project_member, require_project_owner
from app.models.project import Project
from app.models.team import Team
from app.models.user import User
from app.utils.notification_utils import (
    create_personal_notification,
    create_project_notification,
)
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.websockets.connection_manager import manager

router = APIRouter()


@router.post("/project/{project_id}/leave", response_model=dict)
def leave_project(
    background_tasks: BackgroundTasks,
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
    recipients = {project.user_id}
    for tm in project.team_members:
        recipients.add(tm.user_id)
    message = {
        "event": "team.member_left",
        "project_id": project.id,
        "project_name": project.name,
        "member": {
            "id": current_user.id,
            "username": current_user.username,
            "avatar_id": current_user.avatar_id,
        },
    }
    background_tasks.add_task(manager.ts_broadcast, list(recipients), message)
    return {"message": "Left project successfully"}


@router.delete("/project/{project_id}/team/{member_id}", response_model=dict)
def delete_team_member(
    member_id: str,
    background_tasks: BackgroundTasks,
    project: Project = Depends(require_project_owner),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if member_id == project.user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the project owner")

    team_member = (
        db.query(Team)
        .filter(Team.project_id == project.id, Team.user_id == member_id)
        .first()
    )
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")

    removed_user = db.query(User).filter(User.id == member_id).first()
    if not removed_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(team_member)
    db.commit()

    title = "Team Member Removed"
    description = f"{removed_user.username} has been removed from project {project.name} by the owner."
    create_project_notification(
        db, title=title, description=description, project_id=project.id
    )

    recipients = {project.user_id}
    for tm in project.team_members:
        recipients.add(tm.user_id)
    recipients.add(member_id)
    message = {
        "event": "team.member_left",
        "project_id": project.id,
        "project_name": project.name,
        "member": {
            "id": removed_user.id,
            "username": removed_user.username,
            "avatar_id": removed_user.avatar_id,
        },
    }
    background_tasks.add_task(manager.ts_broadcast, list(recipients), message)

    return {"message": "Team member removed successfully"}
