from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "Agora"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # URLs
    APP_URL: str = "http://localhost:8000"  # Backend URL for OAuth callbacks
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for redirects

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "test"  # Using "test" so data is visible in Railway UI

    @property
    def MONGODB_URI(self) -> str:
        """Alias for backwards compatibility."""
        return self.MONGODB_URL

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

    # Tavily (Web Search)
    TAVILY_API_KEY: str = ""
    TAVILY_SEARCH_DEPTH: str = "advanced"  # basic | advanced
    TAVILY_MAX_RESULTS: int = 5

    # Together.ai (Image Generation - Nano Banana Pro)
    TOGETHER_API_KEY: str = ""
    TOGETHER_IMAGE_MODEL: str = "google/gemini-3-pro-image"

    # Meta (Facebook/Instagram) Integration
    # NOTE: These are AGORA APP credentials from Meta Developer Portal
    # NOT client credentials - clients connect via OAuth and their tokens
    # are stored per-company in MongoDB 'integrations' collection
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""

    # Google Calendar Integration
    # NOTE: These are AGORA APP credentials from Google Cloud Console
    # NOT client credentials - clients connect via OAuth and their tokens
    # are stored per-company in MongoDB 'integrations' collection
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
