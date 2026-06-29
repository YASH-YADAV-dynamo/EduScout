from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
WIDGETS_DIR = Path(__file__).resolve().parent / "widgets"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Study Abroad Agent"
    debug: bool = False

    # --- Supabase (required) ---
    supabase_url: str = ""
    supabase_service_key: str = ""
    # Optional: set in Supabase Dashboard → Webhooks to verify incoming events
    supabase_webhook_secret: str = ""

    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_verify_token: str = "study-abroad-verify"

    telegram_bot_token: str = ""
    telegram_bot_username: str = "StudyAbroadAgentBot"
    upload_dir: Path = ROOT_DIR / "uploads"
    # Prefer PUBLIC_BASE_URL — avoids shell BASE_URL=localhost overriding .env via ngrok.
    public_base_url: str = ""
    base_url: str = "http://localhost:8000"
    mcp_oauth_enabled: bool = True
    google_client_id: str = ""
    google_client_secret: str = ""

    @computed_field
    @property
    def effective_base_url(self) -> str:
        return (self.public_base_url or self.base_url).rstrip("/")

    @computed_field
    @property
    def oauth_active(self) -> bool:
        return bool(
            self.mcp_oauth_enabled
            and self.google_client_id
            and self.google_client_secret
            and self.effective_base_url
        )


settings = Settings()
