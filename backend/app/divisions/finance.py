from datetime import datetime, timedelta

from sqlalchemy import select

from app.divisions.base import Division, DivisionEvent
from app.models import FinanceTransaction, TransactionType


class FinanceDivision(Division):
    name = "finance"
    is_sensitive = True  # synthesized suggestions about money — see DESIGN.md

    def _recent_transactions(self, days: int = 30) -> list[FinanceTransaction]:
        since = datetime.utcnow() - timedelta(days=days)
        stmt = select(FinanceTransaction).where(
            FinanceTransaction.occurred_at >= since
        ).order_by(FinanceTransaction.occurred_at.desc())
        return list(self.db.scalars(stmt))

    def summarize_recent_activity(self) -> str:
        txns = self._recent_transactions()
        if not txns:
            return "No transactions logged in the last 30 days."
        income = sum(t.amount for t in txns if t.type == TransactionType.income)
        expense = sum(t.amount for t in txns if t.type == TransactionType.expense)
        return (
            f"Last 30 days: {income:.2f} income, {expense:.2f} expenses "
            f"across {len(txns)} transactions."
        )

    def collect_candidate_events(self) -> list[DivisionEvent]:
        txns = self._recent_transactions(days=30)
        events: list[DivisionEvent] = []

        expense = sum(t.amount for t in txns if t.type == TransactionType.expense)
        income = sum(t.amount for t in txns if t.type == TransactionType.income)

        # Placeholder threshold logic — no budget model exists yet (v1 has
        # no FinanceBudget table). This is a stand-in until budgets are
        # actually implemented; flagged here rather than silently guessed.
        if income and expense > income:
            events.append(
                DivisionEvent(
                    division=self.name,
                    fact=f"Expenses ({expense:.2f}) exceeded income ({income:.2f}) over the last 30 days.",
                    stakes="high",  # money — per DESIGN.md, always surfaced, never auto-resolved
                )
            )

        return events
