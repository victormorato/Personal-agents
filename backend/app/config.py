from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    anthropic_api_key: str
    api_auth_token: str

    fcm_server_key: str = ""

    # How often the Render cron worker checks for CEO-worthy events.
    # Starting assumption per DESIGN.md — adjust without a redesign.
    event_check_interval_hours: int = 1

    # Google Sheets sync (see DESIGN.md — Google Sheets integration).
    # Empty by default: sync no-ops gracefully until both are configured,
    # rather than crashing the app on startup like the other secrets do —
    # this one's genuinely optional, not required for the app to function.
    google_service_account_json: str = ""
    google_sheet_id: str = ""


settings = Settings()
