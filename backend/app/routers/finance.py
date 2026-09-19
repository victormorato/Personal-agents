import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import sheets
from app.auth import require_auth
from app.database import get_db
from app.divisions.finance import FinanceDivision
from app.models import Account, Budget, FinanceTransaction, TransactionType
from app.schemas import (
    AccountOut,
    BudgetIn,
    BudgetOut,
    DivisionResponse,
    FinanceTransactionIn,
    FinanceTransactionOut,
    SheetSyncResult,
)

router = APIRouter(prefix="/finance", tags=["finance"], dependencies=[Depends(require_auth)])


@router.post("/transactions", response_model=FinanceTransactionOut)
def create_transaction(payload: FinanceTransactionIn, db: Session = Depends(get_db)):
    txn = FinanceTransaction(**payload.model_dump())
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.get("/transactions", response_model=list[FinanceTransactionOut])
def list_transactions(db: Session = Depends(get_db)):
    stmt = select(FinanceTransaction).order_by(FinanceTransaction.occurred_at.desc()).limit(200)
    return list(db.scalars(stmt))


@router.post("/transactions/import-csv", response_model=list[FinanceTransactionOut])
async def import_csv(file: UploadFile, db: Session = Depends(get_db)):
    """Expects columns: type,category,amount,description,occurred_at
    (occurred_at as ISO 8601). This is a minimal parser for v1 — no
    per-bank-export format detection, that's a later refinement once real
    statements are tested against it."""
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))
    created = []
    for row in reader:
        txn = FinanceTransaction(
            type=TransactionType(row["type"]),
            category=row["category"],
            amount=float(row["amount"]),
            description=row.get("description"),
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
        )
        db.add(txn)
        created.append(txn)
    db.commit()
    for txn in created:
        db.refresh(txn)
    return created


@router.get("/summary", response_model=DivisionResponse)
def summary(db: Session = Depends(get_db)):
    division = FinanceDivision(db)
    return DivisionResponse(
        summary=division.summarize_recent_activity(),
        disclaimer=division.disclaimer(),
    )


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return list(db.scalars(select(Account).order_by(Account.name)))


@router.post("/budgets", response_model=BudgetOut)
def upsert_budget(payload: BudgetIn, db: Session = Depends(get_db)):
    """Create or update the budget for a category — category is unique, so
    posting the same category again just updates the limit."""
    budget = db.scalar(select(Budget).where(Budget.category == payload.category))
    if budget is None:
        budget = Budget(**payload.model_dump())
        db.add(budget)
    else:
        budget.monthly_limit = payload.monthly_limit
    db.commit()
    db.refresh(budget)
    return budget


@router.get("/budgets", response_model=list[BudgetOut])
def list_budgets(db: Session = Depends(get_db)):
    return list(db.scalars(select(Budget).order_by(Budget.category)))


@router.post("/sync-sheet", response_model=SheetSyncResult)
def sync_sheet(db: Session = Depends(get_db)):
    """Also reachable directly for manual testing — the Render cron job
    calls this same logic on the same cadence as the CEO event-check (see
    DESIGN.md — Google Sheets integration, sync trigger)."""
    return sheets.sync(db)
