import httpx

from app.config import settings


def send_push_notification(title: str, body: str, device_token: str) -> None:
    """Sends a push via Firebase Cloud Messaging (the standard choice for
    Android — see DESIGN.md, second-tier decisions). Requires FCM_SERVER_KEY
    and a registered device token from the Android app; both are stubs
    until the Android app exists to produce a real device token.
    """
    if not settings.fcm_server_key or not device_token:
        # No-op until FCM is actually configured — avoids crashing the
        # cron worker before the Android app can register a device token.
        return

    httpx.post(
        "https://fcm.googleapis.com/fcm/send",
        headers={
            "Authorization": f"key={settings.fcm_server_key}",
            "Content-Type": "application/json",
        },
        json={
            "to": device_token,
            "notification": {"title": title, "body": body},
        },
        timeout=10,
    )
