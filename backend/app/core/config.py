from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "Agora"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # MongoDB (MONGO_URL is Railway's default variable name)
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "agora"

    @property
    def MONGODB_URI(self) -> str:
        """Alias for MONGO_URL for backwards compatibility."""
        return self.MONGO_URL

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
