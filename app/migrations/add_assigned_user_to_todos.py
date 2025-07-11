import logging
from sqlalchemy import inspect, text
from app.database.db import engine

logger = logging.getLogger(__name__)


def upgrade():
    """Apply the migration – add assigned_user_id column and FK if missing."""
    with engine.connect() as connection:
        inspector = inspect(connection)
        columns = [col["name"] for col in inspector.get_columns("todos")]

        if "assigned_user_id" not in columns:
            try:
                with connection.begin():
                    connection.execute(
                        text("ALTER TABLE todos ADD COLUMN assigned_user_id VARCHAR(36)")
                    )
                    connection.execute(
                        text(
                            "ALTER TABLE todos ADD CONSTRAINT fk_todos_assigned_user FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL"
                        )
                    )
                    connection.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_todos_assigned_user_id ON todos (assigned_user_id)"
                        )
                    )
                logger.info("Migration for 'assigned_user_id' applied successfully.")
            except Exception as e:
                logger.error(f"Migration for 'assigned_user_id' failed: {e}")
        else:
            logger.info("Column 'assigned_user_id' already exists, skipping migration.")


def downgrade():
    """Revert the migration – drop FK, column, and index if present."""
    with engine.connect() as connection:
        inspector = inspect(connection)
        columns = [col["name"] for col in inspector.get_columns("todos")]

        if "assigned_user_id" in columns:
            try:
                with connection.begin():
                    connection.execute(
                        text("ALTER TABLE todos DROP CONSTRAINT IF EXISTS fk_todos_assigned_user")
                    )
                    connection.execute(
                        text("DROP INDEX IF EXISTS idx_todos_assigned_user_id ON todos")
                    )
                    connection.execute(text("ALTER TABLE todos DROP COLUMN assigned_user_id"))
                logger.info("Migration for 'assigned_user_id' reverted successfully.")
            except Exception as e:
                logger.error(f"Reverting migration for 'assigned_user_id' failed: {e}")
        else:
            logger.info("Column 'assigned_user_id' does not exist, skipping reversion.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()