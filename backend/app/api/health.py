"""
Health check endpoints
"""
from fastapi import APIRouter
from datetime import datetime
import sys
import os

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Blog Assistant - Investment MVP",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system information"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Blog Assistant - Investment MVP",
        "version": "1.0.0",
        "python_version": sys.version,
        "environment": {
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "database_url": os.getenv("DATABASE_URL", "sqlite:///./investment_blog.db")
        }
    }