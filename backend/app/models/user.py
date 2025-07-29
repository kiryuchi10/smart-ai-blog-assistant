"""
User management models for authentication and subscription handling
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class User(Base):
    """User model with subscription tracking"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    subscription_tier = Column(String(50), default='free')
    subscription_status = Column(String(50), default='active')
    posts_used_this_month = Column(Integer, default=0)
    posts_limit = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    blog_posts = relationship("BlogPost", back_populates="user", cascade="all, delete-orphan")
    scheduled_posts = relationship("ScheduledPost", back_populates="user", cascade="all, delete-orphan")
    platform_integrations = relationship("PlatformIntegration", back_populates="user", cascade="all, delete-orphan")
    
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
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    price_monthly = Column(DECIMAL(10, 2))
    posts_limit = Column(Integer, nullable=False)
    features = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, price={self.price_monthly})>"