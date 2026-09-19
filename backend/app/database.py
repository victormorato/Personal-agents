from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_startup_migrations():
    """Base.metadata.create_all() only creates missing tables — it never
    alters an existing one. There's no Alembic here (not worth it at this
    project's size yet), so new columns on already-created tables get a
    small, idempotent, hand-written ALTER here instead. Must run AFTER
    create_all() so any new table a column references (e.g. accounts)
    already exists."""
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE finance_transactions "
            "ADD COLUMN IF NOT EXISTS account_id INTEGER REFERENCES accounts(id)"
        ))
        conn.execute(text(
            "ALTER TABLE finance_transactions "
            "ADD COLUMN IF NOT EXISTS sheet_row_id VARCHAR(64) UNIQUE"
        ))
