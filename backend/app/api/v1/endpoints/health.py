"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
import structlog

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "AI Blog Assistant API",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check including dependencies"""
    health_status = {
        "status": "healthy",
        "service": "AI Blog Assistant API",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check database connection
    try:
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check file system monitoring directories
    try:
        import os
        monitoring_paths = [
            settings.MONITORED_FOLDERS_PATH,
            settings.PUBLISHED_FOLDERS_PATH,
            settings.FAILED_FOLDERS_PATH
        ]
        
        for path in monitoring_paths:
            if not os.path.exists(path):
                raise Exception(f"Monitoring directory does not exist: {path}")
        
        health_status["checks"]["file_system"] = {"status": "healthy"}
    except Exception as e:
        logger.error("File system health check failed", error=str(e))
        health_status["checks"]["file_system"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    return health_status