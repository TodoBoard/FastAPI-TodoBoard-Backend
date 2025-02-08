from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models import User, Team
from app.auth.token import get_current_user
from app.utils.project import get_project
import uuid

router = APIRouter()


@router.post("/project/{project_id}/team-member/{team_member_id}") # TODO: Switch to an Invite Link system
def add_team_member(
    project_id: str,
    team_member_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can add team members",
        )
    target_user = db.query(User).filter(User.id == team_member_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if any(tm.user_id == team_member_id for tm in project.team_members):
        raise HTTPException(status_code=400, detail="User is already a team member")
    new_team_member = Team(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=team_member_id,
    )
    db.add(new_team_member)
    db.commit()
    return {"message": "Team member added successfully"}


@router.delete("/project/{project_id}/team-member/{team_member_id}")
def delete_team_member(
    project_id: str,
    team_member_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can delete team members",
        )
    team_member_record = next(
        (tm for tm in project.team_members if tm.user_id == team_member_id), None
    )
    if team_member_record is None:
        raise HTTPException(status_code=404, detail="Team member not found")
    db.delete(team_member_record)
    db.commit()
    return {"message": "Team member removed successfully"}
