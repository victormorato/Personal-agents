from datetime import datetime, timedelta

from sqlalchemy import select

from app.divisions.base import Division, DivisionEvent
from app.models import ExerciseLog


class ExerciseDivision(Division):
    name = "exercise"
    is_sensitive = False  # logging/tracking, not medical judgment

    def _recent_logs(self, days: int = 7) -> list[ExerciseLog]:
        since = datetime.utcnow() - timedelta(days=days)
        stmt = select(ExerciseLog).where(ExerciseLog.occurred_at >= since).order_by(
            ExerciseLog.occurred_at.desc()
        )
        return list(self.db.scalars(stmt))

    def summarize_recent_activity(self) -> str:
        logs = self._recent_logs()
        if not logs:
            return "No workouts logged in the last 7 days."
        total_minutes = sum(log.duration_minutes for log in logs)
        activities = ", ".join(sorted({log.activity_type for log in logs}))
        return (
            f"{len(logs)} workouts in the last 7 days, {total_minutes:.0f} "
            f"total minutes. Activities: {activities}."
        )

    def collect_candidate_events(self) -> list[DivisionEvent]:
        logs = self._recent_logs(days=3)
        events: list[DivisionEvent] = []

        if not logs:
            events.append(
                DivisionEvent(
                    division=self.name,
                    fact="No workouts logged in 3 days.",
                    stakes="low",
                )
            )

        # Simple streak-break heuristic: a 7-day streak followed by 2+ quiet
        # days is worth the CEO's attention, not necessarily a push.
        week_logs = self._recent_logs(days=10)
        if len(week_logs) >= 5 and not logs:
            events.append(
                DivisionEvent(
                    division=self.name,
                    fact="Was averaging 5+ workouts/week, now quiet for 3 days.",
                    stakes="low",
                )
            )

        return events
