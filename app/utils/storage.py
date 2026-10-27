"""Cloudflare R2 storage for todo attachments with hard quota enforcement.

Why the bucket can never grow past STORAGE_GLOBAL_LIMIT_BYTES:

1. Only the backend holds R2 credentials. Clients can write solely through
   presigned PUT URLs, each bound to one object key, one Content-Type and one
   exact Content-Length (both are part of the signature).
2. Before a URL is issued, a row with that size is inserted under a Postgres
   advisory lock, after checking SUM(size) of all rows + new size <= limit.
3. A row is only removed after its object was deleted from R2 *and* its upload
   URL has long expired (DELETE_GRACE), so no URL can re-create a deleted object.
   => SUM(size) over all rows is always >= the real bucket size.
4. Daily reconciliation lists the bucket, deletes objects without a row and
   adds any unexplained difference to the used size (safety net).
"""

import logging
import os
import uuid
from datetime import datetime, timedelta

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from fastapi import HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database.db import SessionLocal, engine
from app.models.attachment import AttachmentStatus, TodoAttachment, UploadCounter
from app.models.todo import Todo

load_dotenv()
logger = logging.getLogger(__name__)

MB = 1024 * 1024

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")

# R2 free tier: 10 GB storage, 1M Class A (writes/lists), 10M Class B (reads) per month.
STORAGE_GLOBAL_LIMIT_BYTES = int(os.getenv("STORAGE_GLOBAL_LIMIT_MB", 8 * 1024)) * MB
STORAGE_PROJECT_LIMIT_BYTES = int(os.getenv("STORAGE_PROJECT_LIMIT_MB", 200)) * MB
MAX_FILE_BYTES = int(os.getenv("STORAGE_MAX_FILE_MB", 5)) * MB
MAX_ATTACHMENTS_PER_TODO = int(os.getenv("STORAGE_MAX_ATTACHMENTS_PER_TODO", 20))
USER_DAILY_UPLOADS = int(os.getenv("STORAGE_USER_DAILY_UPLOADS", 50))
GLOBAL_MONTHLY_UPLOADS = int(os.getenv("STORAGE_GLOBAL_MONTHLY_UPLOADS", 200_000))

UPLOAD_URL_EXPIRY = timedelta(minutes=5)
DOWNLOAD_URL_EXPIRY = timedelta(hours=1)
# Must be well above UPLOAD_URL_EXPIRY, see point 3 above.
DELETE_GRACE = timedelta(minutes=30)

# No SVG/HTML: those could run scripts when opened.
ALLOWED_CONTENT_TYPES = {
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "image/webp": [b"RIFF"],
    "application/pdf": [b"%PDF-"],
}

QUOTA_LOCK_ID = 7_243_001
MAINTENANCE_LOCK_ID = 7_243_002

# Bucket bytes the DB does not account for, stored by reconcile so every worker sees it.
UNACCOUNTED_KB_KEY = "reconcile:unaccounted_kb"


def is_configured() -> bool:
    return all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET])


def _require_configured():
    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File uploads are not available",
        )


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                # Newer boto3 versions add checksum headers R2 presigned URLs don't expect.
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )
    return _client


def _increment_counter(db: Session, key: str) -> int:
    stmt = (
        insert(UploadCounter)
        .values(key=key, count=1)
        .on_conflict_do_update(
            index_elements=[UploadCounter.key],
            set_={"count": UploadCounter.count + 1},
        )
        .returning(UploadCounter.count)
    )
    return db.execute(stmt).scalar_one()


def _quota_error(detail: str):
    return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail)


def get_used_bytes(db: Session) -> int:
    reserved = db.query(func.coalesce(func.sum(TodoAttachment.size), 0)).scalar()
    unaccounted_kb = (
        db.query(UploadCounter.count).filter(UploadCounter.key == UNACCOUNTED_KB_KEY).scalar() or 0
    )
    return reserved + unaccounted_kb * 1024


def get_attachment_counts(db: Session, todo_ids: list[str]) -> dict[str, int]:
    if not todo_ids:
        return {}
    rows = (
        db.query(TodoAttachment.todo_id, func.count(TodoAttachment.id))
        .filter(
            TodoAttachment.todo_id.in_(todo_ids),
            TodoAttachment.status == AttachmentStatus.UPLOADED,
        )
        .group_by(TodoAttachment.todo_id)
        .all()
    )
    return dict(rows)


def create_upload(
    db: Session, todo: Todo, user_id: str, filename: str, content_type: str, size: int
) -> tuple[TodoAttachment, str]:
    """Reserves quota for a new attachment and returns it with a presigned PUT URL."""
    _require_configured()

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="File type not allowed")
    if size <= 0 or size > MAX_FILE_BYTES:
        raise _quota_error(f"File too large (max {MAX_FILE_BYTES // MB} MB)")

    # Serializes all reservations, so concurrent uploads can't overshoot a limit.
    db.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": QUOTA_LOCK_ID})

    try:
        if get_used_bytes(db) + size > STORAGE_GLOBAL_LIMIT_BYTES:
            logger.warning("Global storage limit reached, rejecting upload")
            raise _quota_error("Storage is currently full, please try again later")

        project_used = (
            db.query(func.coalesce(func.sum(TodoAttachment.size), 0))
            .join(Todo, TodoAttachment.todo_id == Todo.id)
            .filter(Todo.project_id == todo.project_id)
            .scalar()
        )
        if project_used + size > STORAGE_PROJECT_LIMIT_BYTES:
            raise _quota_error(
                f"Project storage limit reached (max {STORAGE_PROJECT_LIMIT_BYTES // MB} MB)"
            )

        todo_count = (
            db.query(func.count(TodoAttachment.id))
            .filter(
                TodoAttachment.todo_id == todo.id,
                TodoAttachment.status != AttachmentStatus.DELETED,
            )
            .scalar()
        )
        if todo_count >= MAX_ATTACHMENTS_PER_TODO:
            raise HTTPException(
                status_code=400,
                detail=f"Too many attachments (max {MAX_ATTACHMENTS_PER_TODO} per todo)",
            )

        now = datetime.utcnow()
        if _increment_counter(db, f"user:{user_id}:{now:%Y-%m-%d}") > USER_DAILY_UPLOADS:
            raise HTTPException(status_code=429, detail="Daily upload limit reached")
        if _increment_counter(db, f"global:{now:%Y-%m}") > GLOBAL_MONTHLY_UPLOADS:
            logger.warning("Global monthly upload limit reached, rejecting upload")
            raise HTTPException(status_code=429, detail="Upload limit reached, please try again later")

        attachment_id = str(uuid.uuid4())
        attachment = TodoAttachment(
            id=attachment_id,
            todo_id=todo.id,
            uploaded_by=user_id,
            object_key=f"projects/{todo.project_id}/todos/{todo.id}/{attachment_id}",
            filename=filename[:255],
            content_type=content_type,
            size=size,
            status=AttachmentStatus.PENDING,
            created_at=now,
        )
        db.add(attachment)
        db.commit()
    except Exception:
        db.rollback()
        raise

    upload_url = _get_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": R2_BUCKET,
            "Key": attachment.object_key,
            "ContentType": content_type,
            "ContentLength": size,
        },
        ExpiresIn=int(UPLOAD_URL_EXPIRY.total_seconds()),
    )
    return attachment, upload_url


def confirm_upload(db: Session, attachment: TodoAttachment) -> TodoAttachment:
    """Verifies the uploaded object matches what was reserved, otherwise discards it."""
    _require_configured()
    if attachment.status == AttachmentStatus.UPLOADED:
        return attachment
    if attachment.status != AttachmentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Attachment is not pending")

    client = _get_client()
    try:
        head = client.head_object(Bucket=R2_BUCKET, Key=attachment.object_key)
    except ClientError:
        raise HTTPException(status_code=400, detail="Upload not found")

    valid = head["ContentLength"] == attachment.size and head.get("ContentType") == attachment.content_type
    if valid:
        prefix = client.get_object(
            Bucket=R2_BUCKET, Key=attachment.object_key, Range="bytes=0-15"
        )["Body"].read()
        signatures = ALLOWED_CONTENT_TYPES[attachment.content_type]
        valid = any(prefix.startswith(sig) for sig in signatures)
        if attachment.content_type == "image/webp":
            valid = valid and prefix[8:12] == b"WEBP"

    if not valid:
        mark_deleted(db, attachment)
        raise HTTPException(status_code=400, detail="Uploaded file does not match")

    attachment.status = AttachmentStatus.UPLOADED
    db.commit()
    db.refresh(attachment)
    return attachment


def mark_deleted(db: Session, attachment: TodoAttachment):
    """Hides the attachment and frees R2 right away. The row (and its quota)
    stays until `purge_deleted` runs after DELETE_GRACE."""
    attachment.status = AttachmentStatus.DELETED
    db.commit()
    try:
        _get_client().delete_object(Bucket=R2_BUCKET, Key=attachment.object_key)
    except (BotoCoreError, ClientError):
        logger.exception("Failed to delete %s from R2, will retry later", attachment.object_key)


def download_url(attachment: TodoAttachment) -> str:
    disposition = "inline" if attachment.content_type.startswith("image/") else "attachment"
    safe_name = attachment.filename.replace('"', "")
    return _get_client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": R2_BUCKET,
            "Key": attachment.object_key,
            "ResponseContentDisposition": f'{disposition}; filename="{safe_name}"',
        },
        ExpiresIn=int(DOWNLOAD_URL_EXPIRY.total_seconds()),
    )


def purge_deleted(db: Session) -> int:
    """Removes objects + rows that are deleted, never confirmed or whose todo is gone.

    Only rows older than DELETE_GRACE are touched, so their upload URL is expired
    and nothing can write to the key anymore.
    """
    if not is_configured():
        return 0

    cutoff = datetime.utcnow() - DELETE_GRACE
    rows = (
        db.query(TodoAttachment)
        .filter(
            TodoAttachment.created_at < cutoff,
            (TodoAttachment.status != AttachmentStatus.UPLOADED)
            | (TodoAttachment.todo_id.is_(None)),
        )
        .limit(1000)
        .all()
    )
    if not rows:
        return 0

    response = _get_client().delete_objects(
        Bucket=R2_BUCKET,
        Delete={"Objects": [{"Key": r.object_key} for r in rows], "Quiet": True},
    )
    failed = {e["Key"] for e in response.get("Errors", [])}
    purged = 0
    for row in rows:
        if row.object_key not in failed:
            db.delete(row)
            purged += 1
    db.commit()
    if failed:
        logger.warning("Failed to delete %d objects from R2, will retry later", len(failed))
    logger.info("Purged %d attachments", purged)
    return purged


def reconcile(db: Session):
    """Compares the real bucket with the DB. Deletes objects without a row and
    counts any remaining difference towards the quota."""
    if not is_configured():
        return

    known = {
        key: size
        for key, size in db.query(TodoAttachment.object_key, TodoAttachment.size).all()
    }
    stray_cutoff = datetime.utcnow() - DELETE_GRACE
    bucket_bytes = 0
    unaccounted = 0
    stray_keys = []

    paginator = _get_client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=R2_BUCKET):
        for obj in page.get("Contents", []):
            bucket_bytes += obj["Size"]
            reserved = known.get(obj["Key"])
            if reserved is None:
                unaccounted += obj["Size"]
                if obj["LastModified"].replace(tzinfo=None) < stray_cutoff:
                    stray_keys.append(obj["Key"])
            elif obj["Size"] > reserved:
                unaccounted += obj["Size"] - reserved

    for i in range(0, len(stray_keys), 1000):
        _get_client().delete_objects(
            Bucket=R2_BUCKET,
            Delete={"Objects": [{"Key": k} for k in stray_keys[i : i + 1000]], "Quiet": True},
        )
    if stray_keys:
        logger.warning("Deleted %d objects without DB row from R2", len(stray_keys))

    db.merge(UploadCounter(key=UNACCOUNTED_KB_KEY, count=-(-unaccounted // 1024)))
    db.commit()
    logger.info(
        "Storage reconciled: bucket %.1f MB, reserved %.1f MB, unaccounted %.1f MB, limit %.1f MB",
        bucket_bytes / MB,
        sum(known.values()) / MB,
        unaccounted / MB,
        STORAGE_GLOBAL_LIMIT_BYTES / MB,
    )


def run_maintenance(full: bool = False):
    """Entry point for the periodic background job. With several gunicorn
    workers only one runs it at a time (Postgres advisory lock)."""
    with engine.connect() as lock_conn:
        locked = lock_conn.execute(
            text("SELECT pg_try_advisory_lock(:id)"), {"id": MAINTENANCE_LOCK_ID}
        ).scalar()
        if not locked:
            return
        db = SessionLocal()
        try:
            while purge_deleted(db) == 1000:
                pass
            if full:
                reconcile(db)
        except Exception:
            db.rollback()
            logger.exception("Storage maintenance failed")
        finally:
            db.close()
            lock_conn.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": MAINTENANCE_LOCK_ID})
