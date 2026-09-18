# Personal Agent Company

A personal daily-assistant "company": a CEO agent orchestrating specialized
divisions (exercise, finance, more later), delivered as a native Android app
backed by a Python/FastAPI service on Render.

See [DESIGN.md](DESIGN.md) for the full set of architectural decisions and
why they were made — read that before changing the shape of anything here.

## Status

Backend skeleton only. Not yet deployed, not yet connected to a real
database, Android app not yet scaffolded. See "Next steps" below.

## Backend — local setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # then fill in real values
uvicorn app.main:app --reload
```

Requires a running Postgres instance for `DATABASE_URL` — either a local
one for development, or the Render-managed instance once provisioned.

## Backend — Render deployment

- **Web service**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Cron job**: `python -m worker.event_check`, on whatever cadence you set
  (starting assumption: hourly — see `EVENT_CHECK_INTERVAL_HOURS` in
  `app/config.py`)
- **Postgres**: managed instance, `DATABASE_URL` wired into both the web
  service and the cron job's environment

Not yet provisioned — next step once the backend skeleton is reviewed.

## API surface (v1)

- `POST /exercise/logs`, `GET /exercise/logs`, `POST /exercise/sync/google-fit` (stub)
- `POST /finance/transactions`, `GET /finance/transactions`,
  `POST /finance/transactions/import-csv`, `GET /finance/summary`
- `POST /ceo/ask` — on-demand question to the CEO
- `POST /ceo/event-check` — manual trigger for the same logic the cron job runs
- `GET /health`

All routes except `/health` require `Authorization: Bearer <API_AUTH_TOKEN>`.

## Next steps

1. Provision Render infra (Postgres, web service, cron job) via the
   connected Render MCP.
2. Deploy and smoke-test the backend against the real database.
3. Scaffold the native Android app (Kotlin) against this API.
4. Google Fit OAuth flow (currently a stub in `routers/exercise.py`).
5. FCM device-token registration (currently a stub in `worker/event_check.py`).
