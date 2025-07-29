"""
Scheduling and platform integration models
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class ScheduledPost(Base):
    """Scheduled post publications across platforms"""
    __tablename__ = "scheduled_posts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(100), nullable=False)  # wordpress, medium, linkedin, twitter
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(100), default='UTC')
    status = Column(String(50), default='pending')  # pending, published, failed, cancelled
    platform_post_id = Column(String(255))  # ID from the external platform
    platform_url = Column(String(500))  # URL of published post
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    post = relationship("BlogPost", back_populates="scheduled_posts")
    user = relationship("User", back_populates="scheduled_posts")
    
    def __repr__(self):
        return f"<ScheduledPost(platform={self.platform}, status={self.status})>"
    
    def can_retry(self):
        """Check if the post can be retried"""
        return self.retry_count < self.max_retries and self.status == 'failed'
    
    def increment_retry(self):
        """Increment retry counter"""
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.status = 'failed'


class PlatformIntegration(Base):
    """Platform integration credentials and settings"""
    __tablename__ = "platform_integrations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(100), nullable=False)  # wordpress, medium, linkedin, twitter
    access_token = Column(Text)  # Encrypted access token
    refresh_token = Column(Text)  # Encrypted refresh token
    token_expires_at = Column(DateTime(timezone=True))
    platform_user_id = Column(String(255))
    platform_username = Column(String(255))
    platform_settings = Column(Text)  # JSON string with platform-specific settings
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="platform_integrations")
    
    def __repr__(self):
        return f"<PlatformIntegration(platform={self.platform}, user_id={self.user_id})>"
    
    def is_token_expired(self):
        """Check if the access token is expired"""
        if not self.token_expires_at:
            return False
        return func.now() > self.token_expires_at
    
    def needs_refresh(self):
        """Check if token needs refresh (expires within 1 hour)"""
        if not self.token_expires_at:
            return False
        return func.now() > (self.token_expires_at - func.interval('1 hour'))