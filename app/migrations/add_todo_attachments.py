import logging
from sqlalchemy import text
from app.database.db import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Apply the migration – create todo_attachments and upload_counters tables."""
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS todo_attachments (
                    id VARCHAR(36) PRIMARY KEY,
                    todo_id VARCHAR(36) REFERENCES todos(id) ON DELETE SET NULL,
                    uploaded_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    object_key VARCHAR(255) NOT NULL UNIQUE,
                    filename VARCHAR(255) NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    size BIGINT NOT NULL,
                    status VARCHAR(16) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP NOT NULL DEFAULT now()
                )
                """
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_todo_attachments_todo_id ON todo_attachments (todo_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_todo_attachments_status ON todo_attachments (status)"
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS upload_counters (
                    key VARCHAR(100) PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
        )
        logger.info("Migration for 'todo_attachments' ensured.")


def downgrade():
    """Revert the migration – drop both tables."""
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS todo_attachments"))
        connection.execute(text("DROP TABLE IF EXISTS upload_counters"))
        logger.info("Migration for 'todo_attachments' reverted successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
