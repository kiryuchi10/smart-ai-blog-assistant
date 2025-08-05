"""
Database models for AI Blog Assistant
"""

from app.core.database import Base
from .user import User, SubscriptionPlan
from .content import BlogPost, ContentTemplate

# Import all models to ensure they're registered with SQLAlchemy
__all__ = [
    "Base",
    "User", 
    "SubscriptionPlan",
    "BlogPost",
    "ContentTemplate",
]