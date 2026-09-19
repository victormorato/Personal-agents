from fastapi import FastAPI

from app.database import Base, engine, run_startup_migrations
from app.routers import ceo, exercise, finance

Base.metadata.create_all(bind=engine)
run_startup_migrations()

app = FastAPI(title="Personal Agent Company")

app.include_router(exercise.router)
app.include_router(finance.router)
app.include_router(ceo.router)


@app.get("/health")
def health():
    return {"status": "ok"}
