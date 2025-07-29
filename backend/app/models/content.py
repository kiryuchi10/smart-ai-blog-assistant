"""
Content management models for blog posts, versions, and templates
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class BlogPost(Base):
    """Blog post model with SEO and content management features"""
    __tablename__ = "blog_posts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    meta_description = Column(String(160))
    keywords = Column(Text)  # Store as JSON string for SQLite compatibility
    status = Column(String(50), default='draft')  # draft, published, scheduled, archived
    post_type = Column(String(50), default='article')  # article, how-to, listicle, opinion, news
    tone = Column(String(50), default='professional')  # professional, casual, technical, conversational
    seo_score = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    reading_time = Column(Integer, default=0)  # in minutes
    slug = Column(String(500), unique=True)
    featured_image_url = Column(String(500))
    is_template = Column(Boolean, default=False)
    template_category = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="blog_posts")
    versions = relationship("PostVersion", back_populates="post", cascade="all, delete-orphan")
    scheduled_posts = relationship("ScheduledPost", back_populates="post", cascade="all, delete-orphan")
    analytics = relationship("PostAnalytics", back_populates="post", cascade="all, delete-orphan")
    seo_metrics = relationship("SEOMetrics", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BlogPost(id={self.id}, title={self.title[:50]})>"
    
    def calculate_reading_time(self):
        """Calculate reading time based on word count (average 200 words per minute)"""
        if self.word_count:
            self.reading_time = max(1, round(self.word_count / 200))
        return self.reading_time
    
    def update_word_count(self):
        """Update word count based on content"""
        if self.content:
            # Simple word count - can be enhanced with more sophisticated text processing
            self.word_count = len(self.content.split())
        return self.word_count


class PostVersion(Base):
    """Post version history for revision tracking"""
    __tablename__ = "post_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    changes_summary = Column(Text)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    post = relationship("BlogPost", back_populates="versions")
    
    def __repr__(self):
        return f"<PostVersion(post_id={self.post_id}, version={self.version_number})>"


class ContentTemplate(Base):
    """Content templates for reusable blog post structures"""
    __tablename__ = "content_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    template_content = Column(Text, nullable=False)
    category = Column(String(100))  # how-to, listicle, review, comparison, etc.
    industry = Column(String(100))  # tech, health, finance, lifestyle, etc.
    tone = Column(String(50), default='professional')
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    variables = Column(JSON)  # Template variables for customization
    seo_guidelines = Column(JSON)  # SEO recommendations for this template type
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ContentTemplate(name={self.name}, category={self.category})>"
    
    def increment_usage(self):
        """Increment usage counter when template is used"""
        self.usage_count += 1