# Personal Agent Company

A personal daily-assistant "company": a CEO agent orchestrating specialized
divisions (exercise, finance, more later), delivered as a native Android app
backed by a Python/FastAPI service on Render.

See [DESIGN.md](DESIGN.md) for the full set of architectural decisions and
why they were made — read that before changing the shape of anything here.

## Status

Backend is built, deployed, and verified end-to-end (logging, CEO reasoning,
disclaimers, the event-check pipeline). Android app is scaffolded — see
[android/README.md](android/README.md) for its own setup (a Firebase project
is required before it will even build). Not yet installed on a device.

**Live backend**: `https://personal-agents-api.onrender.com`

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
one for development, or the Render-managed instance.

## Backend — Render deployment (done)

- **Web service** (`personal-agents-api`): `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Cron job** (`personal-agents-event-check`): `cd backend && python -m worker.event_check`, hourly at :07 (see `EVENT_CHECK_INTERVAL_HOURS` in `app/config.py`)
- **Postgres** (`personal-agents-db`): paid persistent plan, `DATABASE_URL` wired into both services

Repo is linked to Render by raw GitHub URL, not through Render's GitHub App —
**auto-deploy on push doesn't fire**. After pushing, trigger a deploy manually
(Render dashboard's "Manual Deploy", or the connected Render MCP's
`trigger_deploy`).

## API surface (v1)

- `POST /exercise/logs`, `GET /exercise/logs`
- `POST /finance/transactions`, `GET /finance/transactions`,
  `POST /finance/transactions/import-csv`, `GET /finance/summary`
- `POST /ceo/ask` — on-demand question to the CEO
- `POST /ceo/event-check` — manual trigger for the same logic the cron job runs
- `GET /ceo/events`, `DELETE /ceo/events/{id}` — the CEO's notification history
- `GET /health` — no auth required

All other routes require `Authorization: Bearer <API_AUTH_TOKEN>`.

## Next steps

1. Install the Android app on a real device (needs a Firebase project first
   — see `android/README.md`).
2. Wire up FCM device-token registration so the cron job can actually push to
   a specific device (currently a stub in `backend/worker/event_check.py`).
3. Exercise the app for real for a while — the decision-support framing,
   the CEO's event-judgment quality, and the stakes-based conflict handling
   are all easier to evaluate with real data than synthetic tests.
