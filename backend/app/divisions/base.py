from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class DivisionEvent:
    """A candidate observation a division is handing up to the CEO for its
    judgment pass — see DESIGN.md, "CEO agent > event definition". The
    division does NOT decide whether this is worth surfacing; it just
    reports what's true. The CEO decides what's worth surfacing."""

    division: str
    fact: str
    stakes: str  # "low" | "high" — division's own guess; CEO can override


class Division(ABC):
    """Base class for a division agent. A division's job is to (a) answer
    direct questions about its domain, and (b) report recent facts for the
    CEO's event-judgment pass. It does NOT push notifications itself —
    only the CEO decides what's worth surfacing (see DESIGN.md)."""

    name: str
    #: Set True for divisions whose output must always carry a
    #: "not a substitute for a professional" disclaimer (medical, legal,
    #: finance — see DESIGN.md "Sensitive-output framing").
    is_sensitive: bool = False

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def summarize_recent_activity(self) -> str:
        """Plain-text summary of recent activity in this division, fed to
        the CEO when it reasons across divisions."""

    @abstractmethod
    def collect_candidate_events(self) -> list[DivisionEvent]:
        """Facts worth the CEO's consideration during the periodic
        event-check (see worker/event_check.py). Not every fact here gets
        surfaced — the CEO applies its own judgment on top."""

    def disclaimer(self) -> str | None:
        if not self.is_sensitive:
            return None
        return (
            "This is decision support based on your own data, not "
            "professional advice — check anything consequential with a "
            "licensed professional before acting on it."
        )
