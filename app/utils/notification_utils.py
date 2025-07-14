from app.models.notification import Notification
from app.models.user_notification import UserNotification
from sqlalchemy.orm import Session
import uuid
from app.websockets.connection_manager import manager


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
            # Real-time push
            manager.ts_send_personal(
                user_id,
                {
                    "event": "notification.new",
                    "notification": {
                        "id": notification.id,
                        "title": notification.title,
                        "description": notification.description,
                        "created_at": notification.created_at.isoformat(),
                        "project_id": notification.project_id,
                    },
                },
            )
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
    # Real-time push for personal notification
    manager.ts_send_personal(
        user_id,
        {
            "event": "notification.new",
            "notification": {
                "id": notification.id,
                "title": notification.title,
                "description": notification.description,
                "created_at": notification.created_at.isoformat(),
                "project_id": notification.project_id,
            },
        },
    )
    return notification
