"""
Content management models for blog posts, versions, and templates
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import UUID, ARRAY
from app.models.base import Base
import uuid


class BlogPost(Base):
    """Blog post model with SEO and content management features"""
    __tablename__ = "blog_posts"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    meta_description = Column(String(160))
    keywords = Column(ARRAY(String), nullable=True)
    status = Column(String(50), default='draft')  # draft, published, scheduled, archived
    post_type = Column(String(50), default='article')  # article, how-to, listicle, opinion, news
    content_source = Column(String(50), default='manual')  # folder, api, manual
    tone = Column(String(50), default='professional')  # professional, casual, technical, conversational
    industry = Column(String(100), nullable=True)
    seo_score = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    reading_time = Column(Integer, default=0)  # in minutes
    folder_path = Column(String(500), nullable=True)
    api_data_sources = Column(ARRAY(String), nullable=True)
    enhancement_applied = Column(Boolean, default=False)
    slug = Column(String(500), unique=True)
    featured_image_url = Column(String(500))
    is_template = Column(Boolean, default=False)
    template_category = Column(String(100))
    
    # Relationships
    user = relationship("User", back_populates="blog_posts")
    scheduled_posts = relationship("ScheduledPost", back_populates="post")
    publishing_results = relationship("PublishingResult", back_populates="post")
    analytics = relationship("PostAnalytics", back_populates="post")
    comment_analyses = relationship("CommentAnalysis", back_populates="post")
    content_recommendations = relationship("ContentRecommendation", back_populates="post")
    performance_summary = relationship("PerformanceSummary", back_populates="post", uselist=False)
    api_data_requests = relationship("APIDataRequest", back_populates="post")
    folder_processing_log = relationship("FolderProcessingLog", back_populates="post", uselist=False)
    
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


class ContentTemplate(Base):
    """Content templates for reusable blog post structures"""
    __tablename__ = "content_templates"
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    template_content = Column(Text, nullable=False)
    category = Column(String(100))  # how-to, listicle, review, comparison, etc.
    template_type = Column(String(50), default='article')  # article, how_to, listicle, etc.
    industry = Column(String(100))  # tech, health, finance, lifestyle, etc.
    tone = Column(String(50), default='professional')
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    performance_score = Column(DECIMAL(5, 2), default=0)
    data_requirements = Column(JSON, nullable=True)  # Required API data fields
    chart_templates = Column(JSON, nullable=True)  # Chart configuration templates
    variables = Column(JSON)  # Template variables for customization
    seo_guidelines = Column(JSON)  # SEO recommendations for this template type
    tags = Column(JSON)  # Template tags for categorization
    placeholders = Column(JSON)  # Extracted placeholders from template content
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    creator = relationship("User")
    
    def __repr__(self):
        return f"<ContentTemplate(name={self.name}, category={self.category})>"
    
    def increment_usage(self):
        """Increment usage counter when template is used"""
        self.usage_count += 1