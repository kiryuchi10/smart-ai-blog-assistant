"""
Database models for the AI Blog Assistant application
"""

# Import all models to ensure they are registered with SQLAlchemy
from .user import User, SubscriptionPlan
from .content import BlogPost, PostVersion, ContentTemplate
from .scheduling import ScheduledPost, PlatformIntegration
from .analytics import PostAnalytics, SEOMetrics

# Export all models for easy importing
__all__ = [
    "User",
    "SubscriptionPlan", 
    "BlogPost",
    "PostVersion",
    "ContentTemplate",
    "ScheduledPost",
    "PlatformIntegration",
    "PostAnalytics",
    "SEOMetrics"
]