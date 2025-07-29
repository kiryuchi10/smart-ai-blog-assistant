"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .core.config import settings
from .core.database import create_tables
from .api.v1.api import api_router

# Create FastAPI application
app = FastAPI(
    title="AI Blog Assistant API",
    description="API for AI-powered blog content generation and management",
    version="1.0.0",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security (skip in test environment)
if settings.environment != "test":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create database tables if they don't exist
    create_tables()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Blog Assistant API is running",
        "environment": settings.environment,
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-blog-assistant-api",
        "version": "1.0.0",
        "environment": settings.environment,
        "debug": settings.debug
    }