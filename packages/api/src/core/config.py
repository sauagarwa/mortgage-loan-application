"""
Application configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Basic settings
    APP_NAME: str = "mortgage-ai"
    DEBUG: bool = False

    # CORS settings
    ALLOWED_HOSTS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/mortgage-ai"

    # Keycloak settings
    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "mortgage-ai"
    KEYCLOAK_CLIENT_ID: str = "mortgage-ai-api"
    KEYCLOAK_CLIENT_ID_UI: str = "mortgage-ai-ui"

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "mortgage-documents"
    MINIO_USE_SSL: bool = False

    # LLM settings
    LLM_PROVIDER: str = "openai"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.1

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def keycloak_openid_config_url(self) -> str:
        return (
            f"{self.KEYCLOAK_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/.well-known/openid-configuration"
        )

    @property
    def keycloak_jwks_url(self) -> str:
        return (
            f"{self.KEYCLOAK_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/certs"
        )

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.KEYCLOAK_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"

    @property
    def database_url_sync(self) -> str:
        """Sync database URL for SQLAdmin."""
        return self.DATABASE_URL.replace("+asyncpg", "")


settings = Settings()
