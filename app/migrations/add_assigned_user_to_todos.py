import logging
from sqlalchemy import inspect, text
from app.database.db import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Apply the migration – add assigned_user_id column and FK if missing."""
    with engine.begin() as connection:
        inspector = inspect(connection)
        columns = [col["name"] for col in inspector.get_columns("todos")]

        if "assigned_user_id" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE todos ADD COLUMN IF NOT EXISTS assigned_user_id VARCHAR(36)"
                )
            )

        existing_fks = [fk["name"] for fk in inspector.get_foreign_keys("todos")]
        if "fk_todos_assigned_user" not in existing_fks:
            connection.execute(
                text(
                    "ALTER TABLE todos ADD CONSTRAINT fk_todos_assigned_user FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL"
                )
            )

        existing_indexes = [idx["name"] for idx in inspector.get_indexes("todos")]
        if "idx_todos_assigned_user_id" not in existing_indexes:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_todos_assigned_user_id ON todos (assigned_user_id)"
                )
            )

        logger.info("Migration for 'assigned_user_id' ensured.")


def downgrade():
    """Revert the migration – drop FK, column, and index if present."""
    with engine.begin() as connection:
        inspector = inspect(connection)
        columns = [col["name"] for col in inspector.get_columns("todos")]

        if "assigned_user_id" in columns:
            connection.execute(
                text("ALTER TABLE todos DROP CONSTRAINT IF EXISTS fk_todos_assigned_user")
            )
            connection.execute(
                text("DROP INDEX IF EXISTS idx_todos_assigned_user_id ON todos")
            )
            connection.execute(text("ALTER TABLE todos DROP COLUMN assigned_user_id"))
            logger.info("Migration for 'assigned_user_id' reverted successfully.")
        else:
            logger.info("Column 'assigned_user_id' does not exist, skipping reversion.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()