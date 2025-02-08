from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.invite import Invite
from app.models.project import Project
from app.models.team import Team
from app.schemas import InviteCreate, InviteResponse, InviteUpdate
from app.auth.token import get_current_user
from app.models.user import User
from datetime import datetime, timedelta
from typing import List
import uuid

router = APIRouter()


@router.post("/project/{project_id}/invite", response_model=InviteResponse)
def create_invite(
    project_id: str,
    invite_data: InviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the project owner can create invites"
        )

    expires_at = None
    if invite_data.duration:
        if invite_data.duration.endswith("h"):
            try:
                hours = int(invite_data.duration[:-1])
                expires_at = datetime.utcnow() + timedelta(hours=hours)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid duration format")
        elif invite_data.duration.endswith("d"):
            try:
                days = int(invite_data.duration[:-1])
                expires_at = datetime.utcnow() + timedelta(days=days)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid duration format")
        else:
            raise HTTPException(status_code=400, detail="Invalid duration format")

    if invite_data.max_usage is not None and invite_data.max_usage <= 0:
        raise HTTPException(
            status_code=400, detail="max_usage must be a positive integer"
        )

    new_invite = Invite(
        id=str(uuid.uuid4()),
        project_id=project_id,
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
    return invite


@router.post("/invite/{invite_id}/join")
def join_invite(
    invite_id: str,
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
    return {"message": "Joined project successfully"}


@router.patch("/invite/{invite_id}", response_model=InviteResponse)
def update_invite(
    invite_id: str,
    invite_update: InviteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    project = db.query(Project).filter(Project.id == invite.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this invite"
        )

    if invite_update.duration is not None:
        if invite_update.duration.endswith("h"):
            try:
                hours = int(invite_update.duration[:-1])
                invite.expires_at = datetime.utcnow() + timedelta(hours=hours)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid duration format")
        elif invite_update.duration.endswith("d"):
            try:
                days = int(invite_update.duration[:-1])
                invite.expires_at = datetime.utcnow() + timedelta(days=days)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid duration format")
        else:
            raise HTTPException(status_code=400, detail="Invalid duration format")

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
    invite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    project = db.query(Project).filter(Project.id == invite.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this invite"
        )
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
