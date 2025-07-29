"""
API v1 router configuration
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, subscription, content, template

api_router = APIRouter()

# Include authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Include subscription routes
api_router.include_router(
    subscription.router,
    prefix="/subscription",
    tags=["subscription"]
)

# Include content generation routes
api_router.include_router(
    content.router,
    prefix="/content",
    tags=["content"]
)

# Include template management routes
api_router.include_router(
    template.router,
    prefix="/templates",
    tags=["templates"]
)