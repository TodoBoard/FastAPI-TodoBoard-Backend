import uuid
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.user_notification import UserNotification


def create_project_notification(
    db: Session, title: str, description: str, project_id: str
) -> Notification:
    notification = Notification(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        project_id=project_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    from app.models.project import Project

    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        recipients = set()
        if project.user:
            recipients.add(project.user.id)
        for team in project.team_members:
            recipients.add(team.user_id)
        for user_id in recipients:
            user_notification = UserNotification(
                user_id=user_id, notification_id=notification.id, read=False
            )
            db.add(user_notification)
        db.commit()
    return notification


def create_personal_notification(
    db: Session, user_id: str, title: str, description: str
) -> Notification:
    notification = Notification(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        project_id=None,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    user_notification = UserNotification(
        user_id=user_id, notification_id=notification.id, read=False
    )
    db.add(user_notification)
    db.commit()
    return notification
