from datetime import datetime, timedelta
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.auth.token import get_current_user
from app.database.db import get_db
from app.dependencies.permissions import require_invite_owner, require_project_owner
from app.models.invite import Invite
from app.models.project import Project
from app.models.team import Team
from app.models.user import User
from app.schemas.invite import InviteCreate, InviteResponse, InviteUpdate
from app.utils.notification_utils import create_project_notification
from app.websockets.connection_manager import manager

router = APIRouter()


def parse_duration(duration: str) -> datetime:
    if duration.endswith("h"):
        try:
            hours = int(duration[:-1])
            return datetime.utcnow() + timedelta(hours=hours)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid duration format")
    elif duration.endswith("d"):
        try:
            days = int(duration[:-1])
            return datetime.utcnow() + timedelta(days=days)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid duration format")
    else:
        raise HTTPException(status_code=400, detail="Invalid duration format")


@router.post("/project/{project_id}/invite", response_model=InviteResponse)
def create_invite(
    invite_data: InviteCreate,
    project: Project = Depends(require_project_owner),
    db: Session = Depends(get_db),
):
    expires_at = parse_duration(invite_data.duration) if invite_data.duration else None
    if invite_data.max_usage is not None and invite_data.max_usage <= 0:
        raise HTTPException(
            status_code=400, detail="max_usage must be a positive integer"
        )
    new_invite = Invite(
        id=str(uuid.uuid4()),
        project_id=project.id,
        expires_at=expires_at,
        max_usage=invite_data.max_usage,
        usage_count=0,
        active=True,
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)
    return new_invite


@router.get("/invite/{invite_id}", response_model=InviteResponse)
def get_invite(invite_id: str, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    project = db.query(Project).filter(Project.id == invite.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    invite_creator_username = project.user.username if project.user else "Unknown"
    return {
        "id": invite.id,
        "project_id": invite.project_id,
        "expires_at": invite.expires_at,
        "max_usage": invite.max_usage,
        "usage_count": invite.usage_count,
        "active": invite.active,
        "project_name": project.name,
        "invite_creator_username": invite_creator_username,
        "invite_creator_avatar_id": project.user.avatar_id if project.user else None,
    }


@router.post("/invite/{invite_id}/join")
def join_invite(
    invite_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not invite.active:
        raise HTTPException(status_code=400, detail="Invite is not active")
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite has expired")
    if invite.max_usage is not None and invite.usage_count >= invite.max_usage:
        raise HTTPException(status_code=400, detail="Invite usage limit reached")
    project = db.query(Project).filter(Project.id == invite.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id == current_user.id or any(
        tm.user_id == current_user.id for tm in project.team_members
    ):
        raise HTTPException(status_code=400, detail="User is already a team member")
    new_team_member = Team(
        id=str(uuid.uuid4()),
        project_id=project.id,
        user_id=current_user.id,
    )
    db.add(new_team_member)
    invite.usage_count += 1
    db.commit()
    title = "User Joined Project"
    description = f"User {current_user.username} has joined the project {project.name}."
    create_project_notification(
        db, title=title, description=description, project_id=project.id
    )

    recipients = {project.user_id}
    for tm in project.team_members:
        recipients.add(tm.user_id)
    recipients.remove(current_user.id)
    message = {
        "event": "team.member_joined",
        "project_id": project.id,
        "project_name": project.name,
        "member": {
            "id": current_user.id,
            "username": current_user.username,
            "avatar_id": current_user.avatar_id,
        },
    }
    background_tasks.add_task(manager.ts_broadcast, list(recipients), message)
    return {"message": "Joined project successfully"}


@router.patch("/invite/{invite_id}", response_model=InviteResponse)
def update_invite(
    invite_update: InviteUpdate,
    invite: Invite = Depends(require_invite_owner),
    db: Session = Depends(get_db),
):
    if invite_update.duration is not None:
        invite.expires_at = parse_duration(invite_update.duration)
    if invite_update.max_usage is not None:
        if invite_update.max_usage <= 0:
            raise HTTPException(
                status_code=400, detail="max_usage must be a positive integer"
            )
        invite.max_usage = invite_update.max_usage
    if invite_update.active is not None:
        invite.active = invite_update.active
    db.commit()
    db.refresh(invite)
    return invite


@router.delete("/invite/{invite_id}")
def delete_invite(
    invite: Invite = Depends(require_invite_owner),
    db: Session = Depends(get_db),
):
    db.delete(invite)
    db.commit()
    return {"message": "Invite deleted successfully"}


@router.get("/project/{project_id}/invites", response_model=List[InviteResponse])
def get_invites_for_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the project owner can view invites"
        )
    invites = db.query(Invite).filter(Invite.project_id == project_id).all()
    return invites
