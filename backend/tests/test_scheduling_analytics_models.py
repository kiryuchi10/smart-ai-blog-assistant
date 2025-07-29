"""
Unit tests for scheduling and analytics models
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.content import BlogPost
from app.models.scheduling import ScheduledPost, PlatformIntegration
from app.models.analytics import PostAnalytics, SEOMetrics
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


@pytest.fixture
def test_blog_post(db_session, test_user):
    """Create a test blog post"""
    post = BlogPost(
        user_id=test_user.id,
        title="Test Blog Post",
        content="This is a test blog post content.",
        status="published"
    )
    db_session.add(post)
    db_session.commit()
    return post


class TestScheduledPost:
    """Test cases for ScheduledPost model"""
    
    def test_scheduled_post_creation(self, db_session, test_user, test_blog_post):
        """Test creating a scheduled post"""
        scheduled_time = datetime.now() + timedelta(hours=2)
        scheduled_post = ScheduledPost(
            post_id=test_blog_post.id,
            user_id=test_user.id,
            platform="wordpress",
            scheduled_time=scheduled_time,
            timezone="UTC"
        )
        db_session.add(scheduled_post)
        db_session.commit()
        
        assert scheduled_post.id is not None
        assert scheduled_post.post_id == test_blog_post.id
        assert scheduled_post.user_id == test_user.id
        assert scheduled_post.platform == "wordpress"
        assert scheduled_post.status == "pending"
        assert scheduled_post.timezone == "UTC"
        assert scheduled_post.retry_count == 0
        assert scheduled_post.max_retries == 3
    
    def test_can_retry(self, db_session, test_user, test_blog_post):
        """Test retry logic for failed posts"""
        scheduled_post = ScheduledPost(
            post_id=test_blog_post.id,
            user_id=test_user.id,
            platform="medium",
            scheduled_time=datetime.now(),
            status="failed",
            retry_count=1,
            max_retries=3
        )
        
        # Should be able to retry (1 < 3)
        assert scheduled_post.can_retry() is True
        
        # Set to max retries
        scheduled_post.retry_count = 3
        assert scheduled_post.can_retry() is False
        
        # Test with successful status
        scheduled_post.status = "published"
        scheduled_post.retry_count = 1
        assert scheduled_post.can_retry() is False
    
    def test_increment_retry(self, db_session, test_user, test_blog_post):
        """Test incrementing retry counter"""
        scheduled_post = ScheduledPost(
            post_id=test_blog_post.id,
            user_id=test_user.id,
            platform="linkedin",
            scheduled_time=datetime.now(),
            status="failed",
            retry_count=1,
            max_retries=3
        )
        
        scheduled_post.increment_retry()
        assert scheduled_post.retry_count == 2
        assert scheduled_post.status == "failed"  # Still failed, not at max
        
        # Increment to max retries
        scheduled_post.increment_retry()
        assert scheduled_post.retry_count == 3
        assert scheduled_post.status == "failed"  # Status should change to failed at max
    
    def test_scheduled_post_relationships(self, db_session, test_user, test_blog_post):
        """Test scheduled post relationships"""
        scheduled_post = ScheduledPost(
            post_id=test_blog_post.id,
            user_id=test_user.id,
            platform="twitter",
            scheduled_time=datetime.now()
        )
        db_session.add(scheduled_post)
        db_session.commit()
        
        # Test relationship to post
        assert scheduled_post.post.title == test_blog_post.title
        
        # Test relationship to user
        assert scheduled_post.user.email == test_user.email
        
        # Test reverse relationships
        db_session.refresh(test_blog_post)
        db_session.refresh(test_user)
        assert len(test_blog_post.scheduled_posts) == 1
        assert len(test_user.scheduled_posts) == 1
    
    def test_scheduled_post_repr(self, db_session, test_user, test_blog_post):
        """Test scheduled post string representation"""
        scheduled_post = ScheduledPost(
            post_id=test_blog_post.id,
            user_id=test_user.id,
            platform="wordpress",
            scheduled_time=datetime.now(),
            status="pending"
        )
        
        repr_str = repr(scheduled_post)
        assert "ScheduledPost" in repr_str
        assert "wordpress" in repr_str
        assert "pending" in repr_str


class TestPlatformIntegration:
    """Test cases for PlatformIntegration model"""
    
    def test_platform_integration_creation(self, db_session, test_user):
        """Test creating a platform integration"""
        expires_at = datetime.now() + timedelta(hours=1)
        integration = PlatformIntegration(
            user_id=test_user.id,
            platform="wordpress",
            access_token="encrypted_access_token",
            refresh_token="encrypted_refresh_token",
            token_expires_at=expires_at,
            platform_user_id="wp_user_123",
            platform_username="testuser",
            platform_settings='{"site_url": "https://example.com"}',
            is_active=True
        )
        db_session.add(integration)
        db_session.commit()
        
        assert integration.id is not None
        assert integration.user_id == test_user.id
        assert integration.platform == "wordpress"
        assert integration.access_token == "encrypted_access_token"
        assert integration.platform_user_id == "wp_user_123"
        assert integration.is_active is True
    
    def test_platform_integration_relationship(self, db_session, test_user):
        """Test platform integration relationship with user"""
        integration = PlatformIntegration(
            user_id=test_user.id,
            platform="medium",
            access_token="token"
        )
        db_session.add(integration)
        db_session.commit()
        
        # Test relationship to user
        assert integration.user.email == test_user.email
        
        # Test reverse relationship
        db_session.refresh(test_user)
        assert len(test_user.platform_integrations) == 1
        assert test_user.platform_integrations[0].platform == "medium"
    
    def test_platform_integration_repr(self, db_session, test_user):
        """Test platform integration string representation"""
        integration = PlatformIntegration(
            user_id=test_user.id,
            platform="linkedin",
            access_token="token"
        )
        
        repr_str = repr(integration)
        assert "PlatformIntegration" in repr_str
        assert "linkedin" in repr_str
        assert str(test_user.id) in repr_str


class TestPostAnalytics:
    """Test cases for PostAnalytics model"""
    
    def test_post_analytics_creation(self, db_session, test_blog_post):
        """Test creating post analytics"""
        analytics = PostAnalytics(
            post_id=test_blog_post.id,
            platform="wordpress",
            views=1000,
            unique_views=800,
            likes=50,
            shares=25,
            comments=10,
            clicks=75,
            bounce_rate=0.3,
            avg_time_on_page=180
        )
        db_session.add(analytics)
        db_session.commit()
        
        assert analytics.id is not None
        assert analytics.post_id == test_blog_post.id
        assert analytics.platform == "wordpress"
        assert analytics.views == 1000
        assert analytics.unique_views == 800
        assert analytics.likes == 50
        assert analytics.bounce_rate == 0.3
        assert analytics.avg_time_on_page == 180
    
    def test_calculate_engagement_rate(self, db_session, test_blog_post):
        """Test engagement rate calculation"""
        analytics = PostAnalytics(
            post_id=test_blog_post.id,
            platform="medium",
            views=1000,
            likes=50,
            shares=25,
            comments=10
        )
        
        # Total engagements: 50 + 25 + 10 = 85
        # Engagement rate: 85 / 1000 = 0.085
        engagement_rate = analytics.calculate_engagement_rate()
        assert engagement_rate == 0.085
        assert analytics.engagement_rate == 0.085
        
        # Test with zero views
        analytics.views = 0
        engagement_rate = analytics.calculate_engagement_rate()
        assert engagement_rate == 0.085  # Should remain unchanged
    
    def test_calculate_ctr(self, db_session, test_blog_post):
        """Test click-through rate calculation"""
        analytics = PostAnalytics(
            post_id=test_blog_post.id,
            platform="linkedin",
            views=1000,
            clicks=75
        )
        
        # CTR: 75 / 1000 = 0.075
        ctr = analytics.calculate_ctr()
        assert ctr == 0.075
        assert analytics.click_through_rate == 0.075
        
        # Test with zero views
        analytics.views = 0
        ctr = analytics.calculate_ctr()
        assert ctr == 0.075  # Should remain unchanged
    
    def test_post_analytics_relationship(self, db_session, test_blog_post):
        """Test post analytics relationship"""
        analytics = PostAnalytics(
            post_id=test_blog_post.id,
            platform="twitter",
            views=500
        )
        db_session.add(analytics)
        db_session.commit()
        
        # Test relationship to post
        assert analytics.post.title == test_blog_post.title
        
        # Test reverse relationship
        db_session.refresh(test_blog_post)
        assert len(test_blog_post.analytics) == 1
        assert test_blog_post.analytics[0].platform == "twitter"
    
    def test_post_analytics_repr(self, db_session, test_blog_post):
        """Test post analytics string representation"""
        analytics = PostAnalytics(
            post_id=test_blog_post.id,
            platform="facebook",
            views=200
        )
        
        repr_str = repr(analytics)
        assert "PostAnalytics" in repr_str
        assert str(test_blog_post.id) in repr_str
        assert "facebook" in repr_str


class TestSEOMetrics:
    """Test cases for SEOMetrics model"""
    
    def test_seo_metrics_creation(self, db_session, test_blog_post):
        """Test creating SEO metrics"""
        seo_metrics = SEOMetrics(
            post_id=test_blog_post.id,
            keyword="test keyword",
            search_volume=1000,
            ranking_position=5,
            previous_position=8,
            impressions=500,
            clicks=25,
            difficulty_score=65,
            search_engine="google",
            country_code="US"
        )
        db_session.add(seo_metrics)
        db_session.commit()
        
        assert seo_metrics.id is not None
        assert seo_metrics.post_id == test_blog_post.id
        assert seo_metrics.keyword == "test keyword"
        assert seo_metrics.search_volume == 1000
        assert seo_metrics.ranking_position == 5
        assert seo_metrics.previous_position == 8
        assert seo_metrics.difficulty_score == 65
        assert seo_metrics.search_engine == "google"
        assert seo_metrics.country_code == "US"
    
    def test_get_position_change(self, db_session, test_blog_post):
        """Test position change calculation"""
        seo_metrics = SEOMetrics(
            post_id=test_blog_post.id,
            keyword="improvement keyword",
            ranking_position=5,
            previous_position=8
        )
        
        # Position improved from 8 to 5 (change = +3)
        change = seo_metrics.get_position_change()
        assert change == 3
        
        # Test position decline
        seo_metrics.ranking_position = 10
        seo_metrics.previous_position = 7
        change = seo_metrics.get_position_change()
        assert change == -3
        
        # Test no previous position
        seo_metrics.previous_position = None
        change = seo_metrics.get_position_change()
        assert change == 0
    
    def test_is_ranking_improved(self, db_session, test_blog_post):
        """Test ranking improvement check"""
        seo_metrics = SEOMetrics(
            post_id=test_blog_post.id,
            keyword="test keyword",
            ranking_position=5,
            previous_position=8
        )
        
        # Position improved (8 -> 5)
        assert seo_metrics.is_ranking_improved() is True
        
        # Position declined (5 -> 8)
        seo_metrics.ranking_position = 8
        seo_metrics.previous_position = 5
        assert seo_metrics.is_ranking_improved() is False
        
        # No change
        seo_metrics.ranking_position = 5
        seo_metrics.previous_position = 5
        assert seo_metrics.is_ranking_improved() is False
    
    def test_calculate_ctr_from_search(self, db_session, test_blog_post):
        """Test CTR calculation from search impressions"""
        seo_metrics = SEOMetrics(
            post_id=test_blog_post.id,
            keyword="search keyword",
            impressions=1000,
            clicks=50
        )
        
        # CTR: 50 / 1000 = 0.05
        ctr = seo_metrics.calculate_ctr_from_search()
        assert ctr == 0.05
        assert seo_metrics.click_through_rate == 0.05
        
        # Test with zero impressions
        seo_metrics.impressions = 0
        ctr = seo_metrics.calculate_ctr_from_search()
        assert ctr == 0.05  # Should remain unchanged
    
    def test_seo_metrics_relationship(self, db_session, test_blog_post):
        """Test SEO metrics relationship"""
        seo_metrics = SEOMetrics(
            post_id=test_blog_post.id,
            keyword="relationship keyword",
            ranking_position=3
        )
        db_session.add(seo_metrics)
        db_session.commit()
        
        # Test relationship to post
        assert seo_metrics.post.title == test_blog_post.title
        
        # Test reverse relationship
        db_session.refresh(test_blog_post)
        assert len(test_blog_post.seo_metrics) == 1
        assert test_blog_post.seo_metrics[0].keyword == "relationship keyword"
    
    def test_seo_metrics_repr(self, db_session, test_blog_post):
        """Test SEO metrics string representation"""
        seo_metrics = SEOMetrics(
            post_id=test_blog_post.id,
            keyword="repr keyword",
            ranking_position=7
        )
        
        repr_str = repr(seo_metrics)
        assert "SEOMetrics" in repr_str
        assert "repr keyword" in repr_str
        assert "7" in repr_str


class TestSchedulingAnalyticsIntegration:
    """Integration tests for scheduling and analytics models"""
    
    def test_complete_publishing_workflow(self, db_session, test_user, test_blog_post):
        """Test complete workflow from scheduling to analytics"""
        # Create platform integration
        integration = PlatformIntegration(
            user_id=test_user.id,
            platform="wordpress",
            access_token="token",
            is_active=True
        )
        db_session.add(integration)
        
        # Schedule the post
        scheduled_post = ScheduledPost(
            post_id=test_blog_post.id,
            user_id=test_user.id,
            platform="wordpress",
            scheduled_time=datetime.now() - timedelta(hours=1),  # Past time (published)
            status="published",
            platform_post_id="wp_123",
            platform_url="https://example.com/post"
        )
        db_session.add(scheduled_post)
        
        # Add analytics data
        analytics = PostAnalytics(
            post_id=test_blog_post.id,
            platform="wordpress",
            views=1500,
            likes=75,
            shares=30,
            comments=15
        )
        analytics.calculate_engagement_rate()
        db_session.add(analytics)
        
        # Add SEO metrics
        seo_metrics = SEOMetrics(
            post_id=test_blog_post.id,
            keyword="test blog post",
            ranking_position=3,
            previous_position=7,
            impressions=2000,
            clicks=100
        )
        seo_metrics.calculate_ctr_from_search()
        db_session.add(seo_metrics)
        
        db_session.commit()
        
        # Verify the complete workflow
        assert scheduled_post.status == "published"
        assert scheduled_post.platform_url is not None
        assert analytics.engagement_rate > 0
        assert seo_metrics.is_ranking_improved() is True
        assert seo_metrics.click_through_rate == 0.05
        
        # Verify relationships
        db_session.refresh(test_blog_post)
        assert len(test_blog_post.scheduled_posts) == 1
        assert len(test_blog_post.analytics) == 1
        assert len(test_blog_post.seo_metrics) == 1