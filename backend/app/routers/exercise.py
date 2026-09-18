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


# No server-side sync endpoint: Health Connect data is read on-device by the
# Android app (on-device permissions, no OAuth/client secret involved), which
# then posts each record to POST /logs above with source="health_connect".
# See DESIGN.md — Exercise division for why this replaced the originally
# planned Google Fit integration.
