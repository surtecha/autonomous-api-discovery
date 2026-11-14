from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", hide_input_in_errors=True)
    database_url: SecretStr = SecretStr("")
    postgres_password: SecretStr | None = None
    backend_api_token: SecretStr
    artifact_root: Path = Path(".runtime/artifacts")
    policy_file: Path = Path("experiments/configs/registry.json")

    @model_validator(mode="after")
    def secure_configuration(self) -> "Settings":
        if len(self.backend_api_token.get_secret_value()) < 32:
            raise ValueError("Backend token must contain at least 32 characters")
        if not self.database_url.get_secret_value() and self.postgres_password:
            from sqlalchemy.engine import URL

            url = URL.create(
                "postgresql+psycopg",
                username="discovery",
                password=self.postgres_password.get_secret_value(),
                host="postgres",
                port=5432,
                database="discovery",
            )
            self.database_url = SecretStr(url.render_as_string(hide_password=False))
        if not self.database_url.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("A PostgreSQL psycopg URL is required")
        return self
