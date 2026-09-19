import calendar
from datetime import datetime, timedelta

from sqlalchemy import select

from app.divisions.base import Division, DivisionEvent
from app.models import Budget, FinanceTransaction, TransactionType


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

    def _projected_budget_overruns(self) -> list[DivisionEvent]:
        """Linear day-of-month extrapolation: if spend-so-far/days-elapsed,
        projected across the full month, would exceed the budget, that's
        worth flagging even before the month actually ends — the whole
        point of a "projection" per DESIGN.md rather than a same-day
        after-the-fact total."""
        budgets = list(self.db.scalars(select(Budget)))
        if not budgets:
            return []

        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        days_elapsed = (now - month_start).days + 1
        days_in_month = calendar.monthrange(now.year, now.month)[1]

        month_txns = list(self.db.scalars(
            select(FinanceTransaction).where(
                FinanceTransaction.occurred_at >= month_start,
                FinanceTransaction.type == TransactionType.expense,
            )
        ))

        events: list[DivisionEvent] = []
        for budget in budgets:
            spent = sum(t.amount for t in month_txns if t.category == budget.category)
            if spent == 0:
                continue
            projected = spent / days_elapsed * days_in_month
            if projected > budget.monthly_limit:
                events.append(
                    DivisionEvent(
                        division=self.name,
                        fact=(
                            f"{budget.category} is projected to reach {projected:.2f} this month "
                            f"({spent:.2f} spent through day {days_elapsed}), over the "
                            f"{budget.monthly_limit:.2f} budget."
                        ),
                        stakes="high",  # money — per DESIGN.md, always surfaced, never auto-resolved
                    )
                )
        return events

    def collect_candidate_events(self) -> list[DivisionEvent]:
        txns = self._recent_transactions(days=30)
        events: list[DivisionEvent] = []

        expense = sum(t.amount for t in txns if t.type == TransactionType.expense)
        income = sum(t.amount for t in txns if t.type == TransactionType.income)

        if income and expense > income:
            events.append(
                DivisionEvent(
                    division=self.name,
                    fact=f"Expenses ({expense:.2f}) exceeded income ({income:.2f}) over the last 30 days.",
                    stakes="high",  # money — per DESIGN.md, always surfaced, never auto-resolved
                )
            )

        events.extend(self._projected_budget_overruns())
        return events
