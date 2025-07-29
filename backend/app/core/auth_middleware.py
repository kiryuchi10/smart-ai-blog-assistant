"""
Authentication middleware for FastAPI routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from typing import Optional

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    token = credentials.credentials
    return AuthService.get_current_user(db, token)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to get current verified user
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if token is provided (optional authentication)
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        return AuthService.get_current_user(db, token)
    except HTTPException:
        return None


def require_subscription_tier(required_tier: str):
    """
    Dependency factory to require specific subscription tier
    """
    async def check_subscription(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        tier_hierarchy = {
            "free": 0,
            "basic": 1,
            "premium": 2
        }
        
        user_tier_level = tier_hierarchy.get(current_user.subscription_tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 0)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription tier '{required_tier}' or higher required"
            )
        
        return current_user
    
    return check_subscription


def check_post_limit():
    """
    Dependency to check if user can create new posts based on subscription limits
    """
    async def verify_post_limit(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.can_create_post():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Monthly post limit reached. Please upgrade your subscription."
            )
        
        return current_user
    
    return verify_post_limit