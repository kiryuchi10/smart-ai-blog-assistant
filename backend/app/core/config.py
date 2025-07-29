"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "AI Blog Assistant"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_blog_assistant"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    jwt_secret_key: str = "your-jwt-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "testserver"]
    
    # External APIs
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 2000
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # File Upload
    max_file_size_mb: int = 10
    upload_folder: str = "uploads"
    
    # Subscription Limits
    free_tier_post_limit: int = 5
    basic_tier_post_limit: int = 50
    premium_tier_post_limit: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name in ['allowed_origins', 'allowed_hosts']:
                return [x.strip() for x in raw_val.split(',')]
            return cls.json_loads(raw_val)


# Create global settings instance
settings = Settings()