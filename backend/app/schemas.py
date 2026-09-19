from datetime import datetime

from pydantic import BaseModel

from app.models import TransactionType


class ExerciseLogIn(BaseModel):
    source: str = "manual"
    activity_type: str
    duration_minutes: float
    calories: float | None = None
    notes: str | None = None
    occurred_at: datetime


class ExerciseLogOut(ExerciseLogIn):
    id: int

    class Config:
        from_attributes = True


class FinanceTransactionIn(BaseModel):
    type: TransactionType
    category: str
    amount: float
    description: str | None = None
    occurred_at: datetime
    account_id: int | None = None


class FinanceTransactionOut(FinanceTransactionIn):
    id: int
    sheet_row_id: str | None = None

    class Config:
        from_attributes = True


class AccountOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class BudgetIn(BaseModel):
    category: str
    monthly_limit: float


class BudgetOut(BudgetIn):
    id: int

    class Config:
        from_attributes = True


class SheetSyncResult(BaseModel):
    status: str
    imported: int | None = None
    pushed: int | None = None


class DivisionResponse(BaseModel):
    """Every division response carries its own disclaimer field per
    DESIGN.md — attached inline, not a one-time banner, so it can't be
    scrolled past and forgotten."""

    summary: str
    disclaimer: str | None = None


class CEOAskIn(BaseModel):
    question: str


class CEOResponse(BaseModel):
    answer: str
    disclaimer: str | None = None


class SurfacedEventOut(BaseModel):
    id: int
    division: str
    summary: str
    stakes: str
    disclaimer: str | None = None
    created_at: datetime
    delivered: bool

    class Config:
        from_attributes = True
