"""Entrypoint for the Render cron job. Runs the CEO's periodic event-check
and pushes anything it decides is worth surfacing (see DESIGN.md — CEO
agent, event-driven trigger model).

Render cron command: python -m worker.event_check
Cadence: set on the Render cron job itself (starting assumption: hourly —
see EVENT_CHECK_INTERVAL_HOURS in app/config.py, though the cron schedule
is configured on Render's side, not read from that setting at runtime yet —
they should be kept in sync manually until this is wired up properly).
"""

from app.ceo import CEOAgent
from app.database import SessionLocal
from worker.push import send_push_notification

# TODO: replace with the real registered device token once the Android app
# exists and can register one with the backend. No device-token storage
# exists yet — this is the last stub blocking real push delivery.
_DEVICE_TOKEN_PLACEHOLDER = ""


def main() -> None:
    db = SessionLocal()
    try:
        agent = CEOAgent(db)
        surfaced = agent.run_event_check()
        for event in surfaced:
            send_push_notification(
                title=f"{event.division.title()} update",
                body=event.summary,
                device_token=_DEVICE_TOKEN_PLACEHOLDER,
            )
            event.delivered = bool(_DEVICE_TOKEN_PLACEHOLDER)
        db.commit()
        print(f"Event check complete: {len(surfaced)} event(s) surfaced.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
