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
    ImportCsvResult,
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


@router.post("/transactions/import-csv", response_model=ImportCsvResult)
async def import_csv(file: UploadFile, db: Session = Depends(get_db)):
    """Expects columns: type,category,amount,description,occurred_at
    (occurred_at as ISO 8601), plus an optional account column (matched or
    created by name). Used both for regular CSV imports and the one-time
    historical backfill from the pre-app years of spreadsheet data (see
    DESIGN.md — Google Sheets integration). Returns a count rather than the
    full created list — a large historical import would otherwise return a
    response body with thousands of objects nobody needs to see.

    This is a minimal parser for v1 — no per-bank-export format detection,
    that's a later refinement once real statements are tested against it."""
    contents = await file.read()
    # utf-8-sig strips a leading BOM if present (harmless no-op otherwise) —
    # Excel and PowerShell's Export-Csv both write one by default on
    # Windows, and a plain "utf-8" decode leaves it attached to the first
    # header name, breaking the row["occurred_at"] lookup with a KeyError.
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8-sig")))
    account_cache: dict[str, Account] = {}
    count = 0
    for row in reader:
        account_id = None
        account_name = (row.get("account") or row.get("Account") or "").strip()
        if account_name:
            account = account_cache.get(account_name)
            if account is None:
                account = db.scalar(select(Account).where(Account.name == account_name))
                if account is None:
                    account = Account(name=account_name)
                    db.add(account)
                    db.flush()
                account_cache[account_name] = account
            account_id = account.id

        txn = FinanceTransaction(
            type=TransactionType(row["type"].strip().lower()),
            category=row["category"],
            amount=float(row["amount"]),
            description=row.get("description") or None,
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            account_id=account_id,
        )
        db.add(txn)
        count += 1
    db.commit()
    return ImportCsvResult(created=count)


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
