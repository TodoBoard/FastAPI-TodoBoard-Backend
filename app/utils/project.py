import uuid
from app.models.project import Project
from app.models.team import Team
from sqlalchemy import or_
from sqlalchemy.orm import Session


def create_project(db: Session, name: str, user_id: str) -> Project:
    project = Project(id=str(uuid.uuid4()), name=name, user_id=user_id)
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


def update_project(db: Session, project: Project, name: str) -> Project:
    project.name = name
    db.commit()
    db.refresh(project)
    return project
