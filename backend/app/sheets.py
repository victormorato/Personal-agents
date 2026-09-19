"""Bidirectional sync with the user's Google Sheet (see DESIGN.md — Google
Sheets integration). Uses the real Sheets API v4 for row-level reads/writes
— a different thing entirely from a chat session's file-level Drive access,
which can't touch individual cells. The sheet itself is expected to have
been simplified to one continuous "Transactions" tab with these columns:

    A: Synced ID | B: Date | C: Account | D: Type | E: Category | F: Amount | G: Description

Row 1 is a header row. A row with a blank Synced ID hasn't been imported
into Postgres yet; sync() fills it in once imported, which is also what
marks the row as "already synced" on the next run.
"""

import json
import uuid
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Account, FinanceTransaction, TransactionType

_SHEET_TAB = "Transactions"
_RANGE = f"{_SHEET_TAB}!A2:G"  # skip the header row


def _get_service():
    if not settings.google_service_account_json or not settings.google_sheet_id:
        return None
    info = json.loads(settings.google_service_account_json)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)


def _get_or_create_account(db: Session, name: str) -> Account:
    name = name.strip()
    account = db.scalar(select(Account).where(Account.name == name))
    if account is None:
        account = Account(name=name)
        db.add(account)
        db.flush()  # need account.id before using it as a FK below
    return account


def _parse_amount(raw: str) -> float:
    cleaned = raw.replace("CA$", "").replace("$", "").replace(",", "").strip()
    return float(cleaned) if cleaned else 0.0


def sync(db: Session) -> dict:
    """Pulls new sheet rows into Postgres, then pushes new Postgres
    transactions out to the sheet. Returns a no-op status rather than
    raising when the sheet isn't configured yet — this feature is
    optional, not required for the app to function (see config.py)."""
    service = _get_service()
    if service is None:
        return {"status": "not_configured"}

    sheet = service.spreadsheets()
    rows = sheet.values().get(
        spreadsheetId=settings.google_sheet_id, range=_RANGE
    ).execute().get("values", [])

    # Two API calls total for the pull side, regardless of row count: one
    # batchUpdate for every Synced ID cell that needs writing, not one
    # update() per row — Sheets' write quota (roughly 60 requests/min/user
    # on the default tier) makes a per-row loop slow and rate-limit-prone
    # once there are more than a handful of rows to import (e.g. the
    # historical backfill's ~4000 transactions).
    imported = 0
    id_writes = []
    for i, row in enumerate(rows, start=2):  # row 2 is the first data row
        row = row + [""] * (7 - len(row))  # pad short rows (trailing blanks are dropped by the API)
        synced_id, date_str, account_name, txn_type, category, amount_str, description = row[:7]
        if synced_id:
            continue  # already synced — v1 doesn't handle edits, see DESIGN.md

        account = _get_or_create_account(db, account_name or "Unknown")
        new_id = str(uuid.uuid4())
        txn = FinanceTransaction(
            type=TransactionType(txn_type.strip().lower() or "expense"),
            category=category or "Other",
            amount=_parse_amount(amount_str),
            description=description or None,
            occurred_at=datetime.fromisoformat(date_str) if date_str else datetime.utcnow(),
            account_id=account.id,
            sheet_row_id=new_id,
        )
        db.add(txn)
        id_writes.append({"range": f"{_SHEET_TAB}!A{i}", "values": [[new_id]]})
        imported += 1

    if id_writes:
        sheet.values().batchUpdate(
            spreadsheetId=settings.google_sheet_id,
            body={"valueInputOption": "RAW", "data": id_writes},
        ).execute()
    db.commit()

    # Same reasoning for the push side — one append() call carrying every
    # pending row's values, not one call per transaction.
    pending = db.scalars(
        select(FinanceTransaction).where(FinanceTransaction.sheet_row_id.is_(None))
    ).all()
    pushed = 0
    if pending:
        account_ids = {t.account_id for t in pending if t.account_id}
        accounts = {a.id: a.name for a in db.scalars(select(Account).where(Account.id.in_(account_ids)))} if account_ids else {}

        push_rows = []
        for txn in pending:
            new_id = str(uuid.uuid4())
            push_rows.append([
                new_id,
                txn.occurred_at.isoformat(),
                accounts.get(txn.account_id, ""),
                txn.type.value,
                txn.category,
                str(txn.amount),
                txn.description or "",
            ])
            txn.sheet_row_id = new_id
            pushed += 1

        sheet.values().append(
            spreadsheetId=settings.google_sheet_id,
            range=f"{_SHEET_TAB}!A:G",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": push_rows},
        ).execute()
    db.commit()

    return {"status": "ok", "imported": imported, "pushed": pushed}
