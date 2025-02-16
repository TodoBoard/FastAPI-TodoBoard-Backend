from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.token import get_current_user
from app.database.db import get_db
from app.models.notification import Notification
from app.models.user_notification import UserNotification
from app.schemas.notification import NotificationResponse

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
        return {"message": "Notification already marked as read"}
    user_notif.read = True
    db.commit()
    return {"message": "Notification marked as read"}
