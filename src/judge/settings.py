from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # GitHub App
    github_app_id: int
    github_private_key: str = ""
    github_private_key_path: str = ""
    github_webhook_secret: str

    # Z.AI / GLM
    zai_api_key: str
    zai_base_url: str = "https://api.z.ai/api/paas/v4"
    zai_model: str = "glm-4.7"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Google Sheets
    google_service_account_json: str = ""
    spreadsheet_id: str = ""

    # E2B
    e2b_api_key: str = ""

    # Operational
    roster_cache_ttl: int = 300
    sandbox_timeout: int = 600
    spec_base_url: str = ""

    @model_validator(mode="after")
    def _load_private_key(self):
        if not self.github_private_key and self.github_private_key_path:
            path = Path(self.github_private_key_path)
            if path.exists():
                self.github_private_key = path.read_text()
        return self


settings = Settings()  # type: ignore[missing-argument]
