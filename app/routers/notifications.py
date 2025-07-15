from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.token import get_current_user
from app.database.db import get_db
from app.models.notification import Notification
from app.models.user_notification import UserNotification
from app.schemas.notification import NotificationResponse
from app.websockets.connection_manager import manager

router = APIRouter()


@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    user_notifs = (
        db.query(UserNotification)
        .join(Notification)
        .filter(UserNotification.user_id == current_user.id)
        .all()
    )
    result = []
    for un in user_notifs:
        notif = un.notification
        result.append(
            NotificationResponse(
                id=notif.id,
                title=notif.title,
                description=notif.description,
                created_at=notif.created_at,
                read=un.read,
                project_id=notif.project_id,
            )
        )
    result.sort(key=lambda n: n.created_at, reverse=True)
    return result


@router.post("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_notif = (
        db.query(UserNotification)
        .filter_by(user_id=current_user.id, notification_id=notification_id)
        .first()
    )
    if not user_notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    if user_notif.read:
        unread_count = (
            db.query(UserNotification)
            .filter_by(user_id=current_user.id, read=False)
            .count()
        )
        return {
            "message": "Notification already marked as read",
            "unread_notifications_count": unread_count,
        }

    user_notif.read = True
    db.commit()

    unread_count = (
        db.query(UserNotification)
        .filter_by(user_id=current_user.id, read=False)
        .count()
    )

    return {
        "message": "Notification marked as read",
        "unread_notifications_count": unread_count,
    }


@router.post("/notifications/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark every unread notification for the current user as read."""
    unread_notifs = (
        db.query(UserNotification)
        .filter_by(user_id=current_user.id, read=False)
        .all()
    )

    if not unread_notifs:
        manager.ts_send_personal(
            current_user.id,
            {"event": "notification.read_all", "unread_notifications_count": 0},
        )
        return {
            "message": "No unread notifications found",
            "unread_notifications_count": 0,
        }

    for un in unread_notifs:
        un.read = True

    db.commit()

    manager.ts_send_personal(
        current_user.id,
        {"event": "notification.read_all", "unread_notifications_count": 0},
    )

    return {
        "message": "All notifications marked as read",
        "unread_notifications_count": 0,
    }
