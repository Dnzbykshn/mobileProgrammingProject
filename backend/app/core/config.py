from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "QuranApp App Service"

    # Database — no hardcoded credentials, must come from .env or environment
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "quranapp_app_clean"
    DB_USER: str = "admin"
    DB_PASSWORD: str  # REQUIRED — no default, must be set via env

    @property
    def DATABASE_URL(self) -> str:
        """Sync URL — used by Alembic and maintenance scripts."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Async URL — used by the FastAPI application."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DB_PARAMS(self) -> dict:
        """Legacy dict format — used by scripts that still use psycopg2."""
        return {
            "host": self.DB_HOST,
            "database": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
            "port": str(self.DB_PORT),
        }

    # AI Services — API key must come from .env or environment
    GEMINI_API_KEY: str  # REQUIRED — no default, must be set via env
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768
    LLM_MODEL: str = "gemini-2.0-flash"

    # Security — Secret key must come from .env or environment
    SECRET_KEY: str  # REQUIRED — no default, must be set via env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Resource service integration
    RESOURCE_SERVICE_ENABLED: bool = True
    RESOURCE_SERVICE_BASE_URL: str = "http://localhost:8100/api/v1"
    RESOURCE_SERVICE_TOKEN: str = ""
    RESOURCE_SERVICE_TIMEOUT_SECONDS: float = 15.0

    # CORS (comma-separated origins + optional regex for local dev hosts)
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:19006"
    CORS_ALLOW_ORIGIN_REGEX: str = r"^https?://(localhost|127\.0\.0\.1|10\.0\.2\.2|192\.168\.\d+\.\d+)(:\d+)?$"

    @property
    def CORS_ALLOW_ORIGINS_LIST(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOW_ORIGINS.split(",")
            if origin.strip()
        ]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
