import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
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


class Account(Base):
    """A real bank/credit account (see DESIGN.md — Google Sheets integration).
    Auto-created by the sheet sync the first time it sees a new account name;
    can also be created directly for manual entries."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Budget(Base):
    """A monthly spending limit for one category — feeds the budget-overrun
    projection in FinanceDivision (see DESIGN.md)."""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), unique=True)
    monthly_limit: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class FinanceTransaction(Base):
    """A transaction from any source: manual entry, CSV import, or the
    Google Sheets sync (see DESIGN.md — finance division data sources)."""

    __tablename__ = "finance_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    category: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    # Shared key with the sheet's "Synced ID" column — NULL means this
    # transaction hasn't been pushed to the sheet yet. See DESIGN.md,
    # Google Sheets integration > Dedup / conflict handling.
    sheet_row_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)


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
