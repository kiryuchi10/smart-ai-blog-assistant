"""
Unit tests for content management models
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.content import BlogPost, PostVersion, ContentTemplate
import uuid


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User"
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestBlogPost:
    """Test cases for BlogPost model"""
    
    def test_blog_post_creation(self, db_session, test_user):
        """Test creating a new blog post"""
        post = BlogPost(
            user_id=test_user.id,
            title="Test Blog Post",
            content="This is a test blog post content with multiple words to test word counting.",
            meta_description="Test meta description",
            keywords=["test", "blog", "content"],
            post_type="article",
            tone="professional"
        )
        db_session.add(post)
        db_session.commit()
        
        assert post.id is not None
        assert post.user_id == test_user.id
        assert post.title == "Test Blog Post"
        assert post.status == "draft"
        assert post.post_type == "article"
        assert post.tone == "professional"
        assert post.seo_score == 0
        assert post.word_count == 0  # Not calculated yet
        assert post.reading_time == 0  # Not calculated yet
    
    def test_update_word_count(self, db_session, test_user):
        """Test word count calculation"""
        content = "This is a test blog post with exactly ten words here."
        post = BlogPost(
            user_id=test_user.id,
            title="Test Post",
            content=content
        )
        
        word_count = post.update_word_count()
        assert word_count == 10
        assert post.word_count == 10
    
    def test_calculate_reading_time(self, db_session, test_user):
        """Test reading time calculation"""
        # Create content with 400 words (should be 2 minutes at 200 words/minute)
        content = " ".join(["word"] * 400)
        post = BlogPost(
            user_id=test_user.id,
            title="Test Post",
            content=content,
            word_count=400
        )
        
        reading_time = post.calculate_reading_time()
        assert reading_time == 2
        assert post.reading_time == 2
        
        # Test minimum reading time (should be at least 1 minute)
        post.word_count = 50
        reading_time = post.calculate_reading_time()
        assert reading_time == 1
    
    def test_blog_post_repr(self, db_session, test_user):
        """Test blog post string representation"""
        post = BlogPost(
            user_id=test_user.id,
            title="This is a very long title that should be truncated in the repr",
            content="Test content"
        )
        db_session.add(post)
        db_session.commit()
        
        repr_str = repr(post)
        assert "BlogPost" in repr_str
        assert str(post.id) in repr_str
        # Title should be truncated to 50 characters
        assert len(post.title[:50]) <= 50
    
    def test_blog_post_relationships(self, db_session, test_user):
        """Test blog post relationships"""
        post = BlogPost(
            user_id=test_user.id,
            title="Test Post",
            content="Test content"
        )
        db_session.add(post)
        db_session.commit()
        
        # Test user relationship
        assert post.user.email == test_user.email
        
        # Test that user has the post in their blog_posts collection
        db_session.refresh(test_user)
        assert len(test_user.blog_posts) == 1
        assert test_user.blog_posts[0].title == "Test Post"


class TestPostVersion:
    """Test cases for PostVersion model"""
    
    def test_post_version_creation(self, db_session, test_user):
        """Test creating a post version"""
        # First create a blog post
        post = BlogPost(
            user_id=test_user.id,
            title="Original Title",
            content="Original content"
        )
        db_session.add(post)
        db_session.commit()
        
        # Create a version
        version = PostVersion(
            post_id=post.id,
            version_number=1,
            title="Original Title",
            content="Original content",
            changes_summary="Initial version",
            word_count=2
        )
        db_session.add(version)
        db_session.commit()
        
        assert version.id is not None
        assert version.post_id == post.id
        assert version.version_number == 1
        assert version.changes_summary == "Initial version"
        assert version.word_count == 2
    
    def test_post_version_relationship(self, db_session, test_user):
        """Test post version relationship with blog post"""
        post = BlogPost(
            user_id=test_user.id,
            title="Test Post",
            content="Test content"
        )
        db_session.add(post)
        db_session.commit()
        
        version = PostVersion(
            post_id=post.id,
            version_number=1,
            title="Test Post",
            content="Test content"
        )
        db_session.add(version)
        db_session.commit()
        
        # Test relationship from version to post
        assert version.post.title == "Test Post"
        
        # Test relationship from post to versions
        db_session.refresh(post)
        assert len(post.versions) == 1
        assert post.versions[0].version_number == 1
    
    def test_post_version_repr(self, db_session, test_user):
        """Test post version string representation"""
        post = BlogPost(
            user_id=test_user.id,
            title="Test Post",
            content="Test content"
        )
        db_session.add(post)
        db_session.commit()
        
        version = PostVersion(
            post_id=post.id,
            version_number=2
        )
        
        repr_str = repr(version)
        assert "PostVersion" in repr_str
        assert str(post.id) in repr_str
        assert "2" in repr_str


class TestContentTemplate:
    """Test cases for ContentTemplate model"""
    
    def test_content_template_creation(self, db_session):
        """Test creating a content template"""
        template = ContentTemplate(
            name="How-to Article Template",
            description="Template for creating how-to articles",
            template_content="# How to {topic}\n\n## Introduction\n{introduction}\n\n## Steps\n{steps}",
            category="how-to",
            industry="tech",
            tone="professional",
            is_public=True,
            variables={"topic": "string", "introduction": "text", "steps": "list"},
            seo_guidelines={"min_words": 800, "keywords_density": 0.02}
        )
        db_session.add(template)
        db_session.commit()
        
        assert template.id is not None
        assert template.name == "How-to Article Template"
        assert template.category == "how-to"
        assert template.industry == "tech"
        assert template.tone == "professional"
        assert template.is_public is True
        assert template.usage_count == 0
        assert template.variables["topic"] == "string"
        assert template.seo_guidelines["min_words"] == 800
    
    def test_increment_usage(self, db_session):
        """Test incrementing template usage counter"""
        template = ContentTemplate(
            name="Test Template",
            template_content="Test content",
            usage_count=5
        )
        
        template.increment_usage()
        assert template.usage_count == 6
        
        template.increment_usage()
        assert template.usage_count == 7
    
    def test_content_template_repr(self, db_session):
        """Test content template string representation"""
        template = ContentTemplate(
            name="Listicle Template",
            template_content="Test content",
            category="listicle"
        )
        
        repr_str = repr(template)
        assert "ContentTemplate" in repr_str
        assert "Listicle Template" in repr_str
        assert "listicle" in repr_str
    
    def test_template_validation(self, db_session):
        """Test template validation requirements"""
        # Test that name is required
        template1 = ContentTemplate(template_content="Test content")
        db_session.add(template1)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
        
        db_session.rollback()
        
        # Test that template_content is required
        template2 = ContentTemplate(name="Test Template")
        db_session.add(template2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestContentModelIntegration:
    """Integration tests for content models"""
    
    def test_full_content_workflow(self, db_session, test_user):
        """Test complete content creation workflow"""
        # Create a template
        template = ContentTemplate(
            name="Article Template",
            template_content="# {title}\n\n{content}",
            category="article"
        )
        db_session.add(template)
        
        # Create a blog post
        post = BlogPost(
            user_id=test_user.id,
            title="My First Article",
            content="This is my first article content.",
            post_type="article",
            status="draft"
        )
        db_session.add(post)
        db_session.commit()
        
        # Update word count and reading time
        post.update_word_count()
        post.calculate_reading_time()
        
        # Create initial version
        version1 = PostVersion(
            post_id=post.id,
            version_number=1,
            title=post.title,
            content=post.content,
            changes_summary="Initial draft",
            word_count=post.word_count
        )
        db_session.add(version1)
        
        # Update post content
        post.content = "This is my updated first article content with more words."
        post.update_word_count()
        post.calculate_reading_time()
        
        # Create second version
        version2 = PostVersion(
            post_id=post.id,
            version_number=2,
            title=post.title,
            content=post.content,
            changes_summary="Added more content",
            word_count=post.word_count
        )
        db_session.add(version2)
        db_session.commit()
        
        # Verify the workflow
        assert post.word_count > version1.word_count
        assert len(post.versions) == 2
        assert post.versions[0].version_number == 1
        assert post.versions[1].version_number == 2
        assert template.usage_count == 0  # Not incremented yet
        
        # Increment template usage
        template.increment_usage()
        assert template.usage_count == 1