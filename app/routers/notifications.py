from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.auth.token import get_current_user
from app.models.notification import Notification
from app.models.user_notification import UserNotification
from app.schemas import NotificationResponse

router = APIRouter()


@router.get("/notifications", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    notifications = db.query(Notification).all()
    result = []
    for notif in notifications:
        user_notif = (
            db.query(UserNotification)
            .filter_by(user_id=current_user.id, notification_id=notif.id)
            .first()
        )
        read_flag = user_notif.read if user_notif else False
        result.append(
            NotificationResponse(
                id=notif.id,
                title=notif.title,
                description=notif.description,
                created_at=notif.created_at,
                read=read_flag,
            )
        )
    return result


@router.post("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = (
        db.query(Notification).filter(Notification.id == notification_id).first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    user_notif = (
        db.query(UserNotification)
        .filter_by(user_id=current_user.id, notification_id=notification_id)
        .first()
    )
    if user_notif:
        if user_notif.read:
            return {"message": "Notification already marked as read"}
        user_notif.read = True
    else:
        user_notif = UserNotification(
            user_id=current_user.id, notification_id=notification_id, read=True
        )
        db.add(user_notif)
    db.commit()
    return {"message": "Notification marked as read"}
