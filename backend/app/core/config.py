"""
Configuration settings for the AI Blog Assistant MVP
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./investment_blog.db"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    YAHOO_FINANCE_API_KEY: Optional[str] = None
    
    # Investment Analysis
    DEFAULT_TICKERS: list = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    ANALYSIS_LOOKBACK_DAYS: int = 30
    
    # Blog Generation
    DEFAULT_BLOG_TONE: str = "professional"
    MAX_BLOG_LENGTH: int = 2000
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()