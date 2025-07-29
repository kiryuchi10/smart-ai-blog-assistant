"""
Analytics and performance tracking models
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class PostAnalytics(Base):
    """Content performance metrics tracking"""
    __tablename__ = "post_analytics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(100))  # wordpress, medium, linkedin, twitter, etc.
    views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    click_through_rate = Column(DECIMAL(5, 4), default=0)  # CTR as decimal (0.1234 = 12.34%)
    engagement_rate = Column(DECIMAL(5, 4), default=0)  # Engagement rate as decimal
    bounce_rate = Column(DECIMAL(5, 4), default=0)  # Bounce rate as decimal
    avg_time_on_page = Column(Integer, default=0)  # Average time in seconds
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    post = relationship("BlogPost", back_populates="analytics")
    
    def __repr__(self):
        return f"<PostAnalytics(post_id={self.post_id}, platform={self.platform})>"
    
    def calculate_engagement_rate(self):
        """Calculate engagement rate based on interactions and views"""
        if self.views > 0:
            total_engagements = (self.likes or 0) + (self.shares or 0) + (self.comments or 0)
            self.engagement_rate = total_engagements / self.views
        return self.engagement_rate
    
    def calculate_ctr(self):
        """Calculate click-through rate"""
        if self.views > 0:
            self.click_through_rate = (self.clicks or 0) / self.views
        return self.click_through_rate


class SEOMetrics(Base):
    """SEO performance tracking and keyword rankings"""
    __tablename__ = "seo_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    search_volume = Column(Integer)  # Monthly search volume
    ranking_position = Column(Integer)  # Current ranking position (1-100+)
    previous_position = Column(Integer)  # Previous ranking position for comparison
    click_through_rate = Column(DECIMAL(5, 4))  # CTR from search results
    impressions = Column(Integer, default=0)  # Search impressions
    clicks = Column(Integer, default=0)  # Clicks from search results
    difficulty_score = Column(Integer)  # Keyword difficulty (1-100)
    search_engine = Column(String(50), default='google')  # google, bing, etc.
    country_code = Column(String(2), default='US')  # Country for localized results
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    post = relationship("BlogPost", back_populates="seo_metrics")
    
    def __repr__(self):
        return f"<SEOMetrics(keyword={self.keyword}, position={self.ranking_position})>"
    
    def get_position_change(self):
        """Get position change from previous measurement"""
        if self.previous_position and self.ranking_position:
            return self.previous_position - self.ranking_position  # Positive = improvement
        return 0
    
    def is_ranking_improved(self):
        """Check if ranking has improved"""
        return self.get_position_change() > 0
    
    def calculate_ctr_from_search(self):
        """Calculate CTR from search impressions"""
        if self.impressions > 0:
            self.click_through_rate = (self.clicks or 0) / self.impressions
        return self.click_through_rate