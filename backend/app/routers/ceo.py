from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.ceo import CEOAgent
from app.database import get_db
from app.models import SurfacedEvent
from app.schemas import CEOAskIn, CEOResponse, SurfacedEventOut

router = APIRouter(prefix="/ceo", tags=["ceo"], dependencies=[Depends(require_auth)])


@router.post("/ask", response_model=CEOResponse)
def ask(payload: CEOAskIn, db: Session = Depends(get_db)):
    agent = CEOAgent(db)
    answer, disclaimer = agent.answer(payload.question)
    return CEOResponse(answer=answer, disclaimer=disclaimer)


@router.post("/event-check")
def event_check(db: Session = Depends(get_db)):
    """Also reachable directly for manual testing — the Render cron job
    calls this same logic via worker/event_check.py on a schedule."""
    agent = CEOAgent(db)
    surfaced = agent.run_event_check()
    return {"surfaced_count": len(surfaced)}


@router.get("/events", response_model=list[SurfacedEventOut])
def list_events(db: Session = Depends(get_db)):
    """History of everything the CEO has surfaced — the Android app's
    notification history view reads this."""
    stmt = select(SurfacedEvent).order_by(SurfacedEvent.created_at.desc()).limit(100)
    return list(db.scalars(stmt))
