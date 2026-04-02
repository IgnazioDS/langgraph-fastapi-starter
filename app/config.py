# EXTENSION POINT: Add new environment variables here.
# Each field corresponds to an env var (by default, uppercase field name).
# Required fields have no default value — the app will fail to start if they're missing.
# Optional fields have default values shown inline.
#
# Never read os.environ directly in any other file. All config lives here.

from pydantic import model_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    # ─── Database ─────────────────────────────────────────────────────────────
    postgres_host: str = "localhost"         # POSTGRES_HOST
    postgres_port: int = 5432               # POSTGRES_PORT
    postgres_db: str = "agentdb"            # POSTGRES_DB
    postgres_user: str = "agent"            # POSTGRES_USER
    postgres_password: str                   # POSTGRES_PASSWORD — required, no default
    database_pool_size: int = 10             # DATABASE_POOL_SIZE

    # ─── LLM ──────────────────────────────────────────────────────────────────
    openai_api_key: str                      # OPENAI_API_KEY — required, no default
    llm_model: str = "gpt-4o-mini"          # LLM_MODEL
    embedding_model: str = "text-embedding-3-small"  # EMBEDDING_MODEL
    tavily_api_key: str | None = None        # TAVILY_API_KEY — optional

    # ─── App ──────────────────────────────────────────────────────────────────
    app_env: str = "development"             # APP_ENV: development | production
    log_level: str = "INFO"                  # LOG_LEVEL
    log_format: str = "json"                 # LOG_FORMAT: json | text

    @model_validator(mode="after")
    def validate_app_env(self) -> "AppConfig":
        if self.app_env not in ("development", "production"):
            raise ValueError(f"APP_ENV must be 'development' or 'production', got: {self.app_env}")
        return self

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_file": ".env", "case_sensitive": False}


# Singleton — imported by everything else. Never instantiated twice.
config = AppConfig()  # type: ignore[call-arg]
