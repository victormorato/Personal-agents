import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExerciseLog(Base):
    """A single workout/activity entry, whether manually logged or synced
    from Google Fit (see DESIGN.md — exercise division data source)."""

    __tablename__ = "exercise_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(20))  # "manual" | "health_connect"
    activity_type: Mapped[str] = mapped_column(String(50))
    duration_minutes: Mapped[float] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class FinanceTransaction(Base):
    """A manually entered or CSV-imported transaction (see DESIGN.md —
    finance division starts manual-only, no live bank connection in v1)."""

    __tablename__ = "finance_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    category: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SurfacedEvent(Base):
    """Something the CEO's judgment pass decided was worth pushing to the
    user. Logged here so the Android app can show a history, and so the
    cron worker doesn't re-notify about the same thing repeatedly."""

    __tablename__ = "surfaced_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    division: Mapped[str] = mapped_column(String(50))  # "exercise" | "finance" | "ceo"
    summary: Mapped[str] = mapped_column(Text)
    stakes: Mapped[str] = mapped_column(String(20))  # "low" | "high" — see DESIGN.md conflict handling
    disclaimer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered: Mapped[bool] = mapped_column(default=False)
