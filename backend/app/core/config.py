# app/core/config.py

from typing import List, Optional, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # Tell Pydantic where to load the .env and that keys are not case-sensitive
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ignore any extra env vars we didn't model
    )

    # -----------------------------
    # Core App
    # -----------------------------
    NODE_ENV: str = "development"
    DEBUG: bool = True
    debug: bool = True  # alias for DEBUG
    environment: str = "development"  # alias for NODE_ENV
    APP_NAME: str = "AI Blog Assistant"
    APP_VERSION: str = "1.0.0"
    API_VERSION: str = "v1"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND_URL: str = "http://localhost:8000"
    API_BASE_URL: str = "http://localhost:8000/api/v1"

    # -----------------------------
    # CORS
    # -----------------------------
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS,PATCH"
    CORS_HEADERS: str = "Content-Type,Authorization,X-Requested-With,Accept"

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def get_cors_methods(self) -> List[str]:
        """Parse CORS methods from comma-separated string"""
        return [method.strip() for method in self.CORS_METHODS.split(",") if method.strip()]

    def get_cors_headers(self) -> List[str]:
        """Parse CORS headers from comma-separated string"""
        return [header.strip() for header in self.CORS_HEADERS.split(",") if header.strip()]

    @property
    def allowed_origins(self) -> List[str]:
        """Get allowed origins for CORS"""
        return self.get_cors_origins()

    @property
    def allowed_hosts(self) -> List[str]:
        """Get allowed hosts"""
        return ["localhost", "127.0.0.1", "0.0.0.0"]

    # -----------------------------
    # Database
    # -----------------------------
    DATABASE_URL: str
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "ai_blog_assistant"
    DATABASE_USER: str = "blog_user"
    DATABASE_PASSWORD: str = ""
    DATABASE_SSL_MODE: str = "prefer"

    # -----------------------------
    # Redis
    # -----------------------------
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @property
    def redis_url(self) -> str:
        """Get Redis URL for Celery and other services"""
        return self.REDIS_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # -----------------------------
    # OpenAI / LLM
    # -----------------------------
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORG_ID: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_TOP_P: float = 1.0
    OPENAI_FREQUENCY_PENALTY: float = 0.0
    OPENAI_PRESENCE_PENALTY: float = 0.0

    # DeepSeek
    DEEPSEEK_BASE_URL: Optional[str] = "https://api.deepseek.com/v1"
    # If you have a separate key:
    DEEPSEEK_API_KEY: Optional[str] = None

    # Seek / Paper2Code
    SEEK_API_KEY: Optional[str] = None

    # -----------------------------
    # Security / Auth
    # -----------------------------
    SECRET_KEY: str = "change_me"
    JWT_SECRET_KEY: str = "change_me_jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "ai-blog-assistant"
    JWT_AUDIENCE: str = "blog-users"

    API_KEY_HEADER: str = "X-API-Key"
    API_RATE_LIMIT_PER_MINUTE: int = 60
    API_RATE_LIMIT_PER_HOUR: int = 500
    API_RATE_LIMIT_PER_DAY: int = 5000

    # -----------------------------
    # Email / SMTP
    # -----------------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: str = "AI Blog Assistant"


# Singleton settings object to import elsewhere
settings = Settings()