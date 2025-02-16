from app.auth.token import get_current_user
from app.database.db import get_db
from app.models.invite import Invite
from app.models.project import Project
from app.models.todo import Todo
from app.models.user import User
from app.utils.project import get_project
from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session


def require_project_member(
    project_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id and not any(
        tm.user_id == current_user.id for tm in project.team_members
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project",
        )
    project.is_owner = project.user_id == current_user.id
    return project


def require_project_owner(
    project_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as project owner",
        )
    project.is_owner = True
    return project


def require_invite_owner(
    invite_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invite:
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    project = db.query(Project).filter(Project.id == invite.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as project owner",
        )
    return invite


def require_todo_permission(
    todo_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Todo:
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    project = todo.project
    if project.user_id != current_user.id and not any(
        tm.user_id == current_user.id for tm in project.team_members
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this todo",
        )
    return todo
