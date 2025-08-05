"""
API v1 router
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Basic health check endpoint
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-blog-assistant-api",
        "version": "1.0.0"
    }