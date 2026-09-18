from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db
from app.models import ExerciseLog
from app.schemas import ExerciseLogIn, ExerciseLogOut

router = APIRouter(prefix="/exercise", tags=["exercise"], dependencies=[Depends(require_auth)])


@router.post("/logs", response_model=ExerciseLogOut)
def create_log(payload: ExerciseLogIn, db: Session = Depends(get_db)):
    log = ExerciseLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/logs", response_model=list[ExerciseLogOut])
def list_logs(db: Session = Depends(get_db)):
    stmt = select(ExerciseLog).order_by(ExerciseLog.occurred_at.desc()).limit(100)
    return list(db.scalars(stmt))


@router.post("/sync/google-fit")
def sync_google_fit():
    """Stub — Google Fit OAuth + data pull happens here. Needs
    GOOGLE_FIT_CLIENT_ID/SECRET configured (see .env.example) and the
    actual OAuth consent flow, which requires real credentials to build
    and test against. Not implemented yet."""
    return {
        "status": "not_implemented",
        "detail": "Google Fit sync requires OAuth credentials to be configured first.",
    }
