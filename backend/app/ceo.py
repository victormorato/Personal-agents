import json

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

        candidate_text = "\n".join(
            f"{i}. [{c.division}/{c.stakes}] {c.fact}" for i, c in enumerate(candidates)
        )
        message = _client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=_SYSTEM_PROMPT
            + "\n\nYou are now doing the periodic event-check. Given the "
            "numbered candidate facts below, decide which (if any) are "
            "actually worth a push notification to the user. Most days, "
            'nothing is. Respond with ONLY a JSON object of the exact form '
            '{"surface": [<indices>]}, where each index is the number of a '
            "candidate fact worth surfacing. Use an empty array if none "
            "qualify. No other text, no markdown code fences, no "
            "explanation — your reasoning is not part of the output, only "
            "the final decision.",
            messages=[{"role": "user", "content": candidate_text}],
        )
        decision_text = message.content[0].text.strip()

        # Parse a strict, schema-free JSON decision rather than free-form
        # lines. A prior line-based format (even with a required prefix)
        # let the model's own reasoning about *not* surfacing something
        # masquerade as a surfaced event, since prose can still match a
        # required prefix while meaning the opposite. Indices into the
        # candidates we already built are unambiguous either way, and
        # content (division/stakes/fact) comes from our own data, never
        # from the model's paraphrase — so a malformed or verbose response
        # can only fail closed (nothing surfaced), never fail open.
        surfaced: list[SurfacedEvent] = []
        try:
            decision = json.loads(decision_text)
            indices = decision["surface"]
        except (json.JSONDecodeError, KeyError, TypeError):
            indices = []

        for i in indices:
            if not isinstance(i, int) or not (0 <= i < len(candidates)):
                continue
            candidate = candidates[i]
            disclaimer = next(
                (d.disclaimer() for d in self.divisions if d.name == candidate.division),
                None,
            )
            event = SurfacedEvent(
                division=candidate.division,
                summary=candidate.fact,
                stakes=candidate.stakes,
                disclaimer=disclaimer,
            )
            self.db.add(event)
            surfaced.append(event)

        if surfaced:
            self.db.commit()

        return surfaced
