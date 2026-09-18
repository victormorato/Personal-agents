from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.divisions.base import Division, DivisionEvent
from app.divisions.exercise import ExerciseDivision
from app.divisions.finance import FinanceDivision
from app.models import SurfacedEvent

_client = Anthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = """You are the CEO of a small personal "company" of agents \
that helps the user manage their daily life. You receive summaries from \
each division and either answer the user's direct question, or (during a \
periodic check) judge whether anything is worth proactively surfacing.

Rules you must follow (see DESIGN.md for the full rationale):
- Resolve conflicts between divisions BY STAKES: low-stakes disagreements \
(e.g. a minor schedule overlap) you resolve yourself and just state the \
resolution. Anything touching health, money, or legal risk you must \
surface explicitly rather than silently deciding — name the tradeoff, \
don't pick a side.
- Any output that touches health, legal, or financial decisions must be \
framed as decision support, not professional advice — you are not a \
substitute for a doctor, lawyer, or financial advisor, and must say so \
when relevant.
- Be concise. This is a daily-use assistant, not a report generator.
"""


class CEOAgent:
    def __init__(self, db: Session):
        self.db = db
        self.divisions: list[Division] = [
            ExerciseDivision(db),
            FinanceDivision(db),
        ]

    def _division_context(self) -> str:
        parts = []
        for division in self.divisions:
            parts.append(f"[{division.name}] {division.summarize_recent_activity()}")
        return "\n".join(parts)

    def answer(self, question: str) -> tuple[str, str | None]:
        """On-demand Q&A — used by POST /ceo/ask."""
        context = self._division_context()
        message = _client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Current state:\n{context}\n\nQuestion: {question}",
                }
            ],
        )
        answer_text = message.content[0].text

        # A response is only disclaimed if it actually drew on a sensitive
        # division — don't slap a finance disclaimer on an exercise-only answer.
        touched_sensitive = any(d.is_sensitive for d in self.divisions)
        disclaimer = None
        if touched_sensitive:
            disclaimer = next(d.disclaimer() for d in self.divisions if d.is_sensitive)

        return answer_text, disclaimer

    def run_event_check(self) -> list[SurfacedEvent]:
        """Called by the Render cron worker (see worker/event_check.py) on
        the cadence set by EVENT_CHECK_INTERVAL_HOURS. The CEO uses its own
        judgment on what's worth surfacing — divisions report candidate
        facts, they don't decide push-worthiness themselves (DESIGN.md)."""
        candidates: list[DivisionEvent] = []
        for division in self.divisions:
            candidates.extend(division.collect_candidate_events())

        if not candidates:
            return []

        candidate_text = "\n".join(f"- [{c.division}/{c.stakes}] {c.fact}" for c in candidates)
        message = _client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=_SYSTEM_PROMPT
            + "\n\nYou are now doing the periodic event-check. Given the "
            "candidate facts below, decide which (if any) are actually "
            "worth a push notification to the user. Most days, nothing is. "
            "Respond with one short line per fact worth surfacing, or "
            "nothing at all if none qualify.",
            messages=[{"role": "user", "content": candidate_text}],
        )
        decision_text = message.content[0].text.strip()

        surfaced: list[SurfacedEvent] = []
        if decision_text:
            for line in decision_text.splitlines():
                line = line.strip("- ").strip()
                if not line:
                    continue
                # Stakes on the persisted event follows the source division's
                # own flag — the CEO's judgment decided IF to surface, this
                # governs how it's displayed/escalated in the app.
                matching = next(
                    (c for c in candidates if c.division in line.lower() or c.fact in line),
                    None,
                )
                stakes = matching.stakes if matching else "low"
                division_name = matching.division if matching else "ceo"
                disclaimer = next(
                    (d.disclaimer() for d in self.divisions if d.name == division_name),
                    None,
                )
                event = SurfacedEvent(
                    division=division_name,
                    summary=line,
                    stakes=stakes,
                    disclaimer=disclaimer,
                )
                self.db.add(event)
                surfaced.append(event)
            self.db.commit()

        return surfaced
