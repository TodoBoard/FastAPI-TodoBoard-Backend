from sqlalchemy.orm import Session
from app.models.project import Project
import uuid
from sqlalchemy import or_
from app.models.team import Team


def create_project(
    db: Session, name: str, user_id: str, description: str | None = None
) -> Project:
    project = Project(
        id=str(uuid.uuid4()), name=name, description=description, user_id=user_id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_projects(db: Session):
    return db.query(Project).all()


def get_project(db: Session, project_id: str) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()


def get_user_projects(db: Session, user_id: str):
    return (
        db.query(Project)
        .filter(
            or_(
                Project.user_id == user_id,
                Project.team_members.any(Team.user_id == user_id),
            )
        )
        .all()
    )


def update_project(
    db: Session, project: Project, name: str, description: str | None = None
) -> Project:
    project.name = name
    project.description = description
    db.commit()
    db.refresh(project)
    return project
