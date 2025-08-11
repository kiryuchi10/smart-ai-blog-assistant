"""
User management models for authentication and subscription handling
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import UUID, ARRAY
from app.models.base import Base
import uuid


class User(Base):
    """User model with subscription tracking"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    subscription_tier = Column(String(50), default='free')
    subscription_status = Column(String(50), default='active')
    subscription_plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True)
    posts_used_this_month = Column(Integer, default=0)
    posts_limit = Column(Integer, default=5)
    api_calls_used_this_month = Column(Integer, default=0, nullable=False)
    api_calls_limit = Column(Integer, default=100, nullable=False)
    folder_monitoring_enabled = Column(Boolean, default=False, nullable=False)
    comment_analysis_enabled = Column(Boolean, default=False, nullable=False)
    advanced_analytics_enabled = Column(Boolean, default=False, nullable=False)
    priority_support_enabled = Column(Boolean, default=False, nullable=False)
    preferred_platforms = Column(ARRAY(String), default=lambda: [], nullable=False)
    default_content_tone = Column(String(50), default='professional', nullable=False)
    default_content_length = Column(String(20), default='medium', nullable=False)
    timezone = Column(String(100), default='UTC', nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    subscription_started_at = Column(DateTime(timezone=True), nullable=True)
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    subscription_plan = relationship("SubscriptionPlan", back_populates="users")
    blog_posts = relationship("BlogPost", back_populates="user")
    scheduled_posts = relationship("ScheduledPost", back_populates="user")
    platform_integrations = relationship("PlatformIntegration", back_populates="user")
    content_recommendations = relationship("ContentRecommendation", back_populates="user")
    api_data_requests = relationship("APIDataRequest", back_populates="user")
    folder_processing_logs = relationship("FolderProcessingLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def can_create_post(self):
        """Check if user can create a new post based on subscription limits"""
        return self.posts_used_this_month < self.posts_limit
    
    def increment_post_usage(self):
        """Increment the monthly post usage counter"""
        self.posts_used_this_month += 1
    
    def reset_monthly_usage(self):
        """Reset monthly post usage counter (called monthly)"""
        self.posts_used_this_month = 0


class SubscriptionPlan(Base):
    """Subscription plans with features and limits"""
    __tablename__ = "subscription_plans"
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    price_monthly = Column(DECIMAL(10, 2))
    price_yearly = Column(DECIMAL(10, 2))
    posts_limit = Column(Integer, nullable=False)
    api_calls_limit = Column(Integer, nullable=False)
    storage_limit_gb = Column(Integer, default=1, nullable=False)
    folder_monitoring = Column(Boolean, default=False, nullable=False)
    comment_analysis = Column(Boolean, default=False, nullable=False)
    advanced_analytics = Column(Boolean, default=False, nullable=False)
    priority_support = Column(Boolean, default=False, nullable=False)
    multi_platform_publishing = Column(Boolean, default=False, nullable=False)
    ai_content_enhancement = Column(Boolean, default=False, nullable=False)
    api_data_integration = Column(Boolean, default=False, nullable=False)
    custom_templates = Column(Boolean, default=False, nullable=False)
    bulk_operations = Column(Boolean, default=False, nullable=False)
    white_label = Column(Boolean, default=False, nullable=False)
    features = Column(JSON, default={}, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_popular = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    trial_days = Column(Integer, default=0, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="subscription_plan")
    
    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, price={self.price_monthly})>"