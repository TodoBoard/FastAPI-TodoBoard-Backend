from app.auth.token import get_current_user
from app.database.db import get_db
from app.dependencies.permissions import require_attachment_permission, require_todo_permission
from app.models import Project, Todo
from app.models.attachment import AttachmentStatus, TodoAttachment
from app.models.user import User
from app.schemas.attachment import (
    AttachmentCreate,
    AttachmentListResponse,
    AttachmentResponse,
    AttachmentUploadResponse,
)
from app.utils import storage
from app.websockets.connection_manager import manager
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _project_recipients(db: Session, project_id: str) -> list[str]:
    project = db.query(Project).filter(Project.id == project_id).first()
    recipients = {project.user_id}
    for tm in project.team_members:
        recipients.add(tm.user_id)
    return list(recipients)


@router.post("/todo/{todo_id}/attachments", response_model=AttachmentUploadResponse)
def create_attachment_upload(
    body: AttachmentCreate,
    todo: Todo = Depends(require_todo_permission),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment, upload_url = storage.create_upload(
        db, todo, current_user.id, body.filename, body.content_type, body.size
    )
    return {
        "attachment": attachment,
        "upload_url": upload_url,
        "upload_headers": {"Content-Type": attachment.content_type},
    }


@router.post("/attachment/{attachment_id}/confirm", response_model=AttachmentResponse)
def confirm_attachment_upload(
    background_tasks: BackgroundTasks,
    attachment: TodoAttachment = Depends(require_attachment_permission),
    db: Session = Depends(get_db),
):
    attachment = storage.confirm_upload(db, attachment)
    attachment.url = storage.download_url(attachment)
    attachment.attachment_count = storage.get_attachment_counts(db, [attachment.todo_id]).get(
        attachment.todo_id, 0
    )

    message = {
        "event": "attachment.created",
        "todo_id": attachment.todo_id,
        "attachment_id": attachment.id,
        "attachment_count": attachment.attachment_count,
    }
    recipients = _project_recipients(db, attachment.todo.project_id)
    background_tasks.add_task(manager.ts_broadcast, recipients, message)
    return attachment


@router.get("/todo/{todo_id}/attachments", response_model=AttachmentListResponse)
def list_attachments(
    todo: Todo = Depends(require_todo_permission),
    db: Session = Depends(get_db),
):
    if not storage.is_configured():
        return {"attachments": []}

    attachments = (
        db.query(TodoAttachment)
        .filter(
            TodoAttachment.todo_id == todo.id,
            TodoAttachment.status == AttachmentStatus.UPLOADED,
        )
        .order_by(TodoAttachment.created_at)
        .all()
    )
    for attachment in attachments:
        attachment.url = storage.download_url(attachment)
    return {"attachments": attachments}


@router.delete("/attachment/{attachment_id}")
def delete_attachment(
    background_tasks: BackgroundTasks,
    attachment: TodoAttachment = Depends(require_attachment_permission),
    db: Session = Depends(get_db),
):
    todo_id = attachment.todo_id
    project_id = attachment.todo.project_id
    storage.mark_deleted(db, attachment)
    attachment_count = storage.get_attachment_counts(db, [todo_id]).get(todo_id, 0)

    message = {
        "event": "attachment.deleted",
        "todo_id": todo_id,
        "attachment_id": attachment.id,
        "attachment_count": attachment_count,
    }
    background_tasks.add_task(manager.ts_broadcast, _project_recipients(db, project_id), message)
    return {"message": "Attachment deleted successfully", "attachment_count": attachment_count}
