import importlib.util
import logging
import os
from app.database.db import Base, engine, SessionLocal
from sqlalchemy import Column, String

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.dirname(__file__)


class Migration(Base):
    __tablename__ = "migrations"
    filename = Column(String, primary_key=True)


def run_migrations():
    """Checks for and applies all new migrations."""
    logger.info("Checking for new migrations...")
    Migration.metadata.create_all(bind=engine)
    db_session = SessionLocal()

    try:
        applied_migrations = {m.filename for m in db_session.query(Migration).all()}

        migration_files = sorted(
            f
            for f in os.listdir(MIGRATIONS_DIR)
            if f.endswith(".py")
            and f != "__init__.py"
            and f != os.path.basename(__file__)
        )

        for filename in migration_files:
            if filename not in applied_migrations:
                logger.info(f"Found new migration: {filename}. Applying...")

                module_name = f"app.migrations.{filename[:-3]}"
                spec = importlib.util.spec_from_file_location(
                    module_name, os.path.join(MIGRATIONS_DIR, filename)
                )
                migration_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(migration_module)

                migration_module.upgrade()

                new_migration = Migration(filename=filename)
                db_session.add(new_migration)
                db_session.commit()
                logger.info(f"Successfully applied {filename}.")

        if not migration_files:
            logger.info("No migration files found.")
        elif not any(f for f in migration_files if f not in applied_migrations):
            logger.info("Database is up to date. No new migrations to apply.")

    finally:
        db_session.close() 