"""
Application configuration using Pydantic BaseSettings
"""
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # Database Configuration
    POSTGRES_URL: str
    REDIS_URL: str
    
    # WordPress Configuration
    WORDPRESS_URL: str = ""
    WORDPRESS_USERNAME: str = ""
    WORDPRESS_APP_PASSWORD: str = ""
    
    # API Keys
    ALPHA_VANTAGE_API: str = ""
    YAHOO_API_KEY: str = ""
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Celery Configuration
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    class Config:
        env_file = ".env"

settings = Settings()