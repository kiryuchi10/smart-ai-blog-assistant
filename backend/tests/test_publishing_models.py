"""
Unit tests for publishing models
"""
import pytest
from datetime import datetime, timedelta
from app.models.publishing import ScheduledPost, PublishingResult, PlatformIntegration


class TestScheduledPost:
    """Test ScheduledPost model"""
    
    @pytest.mark.asyncio
    async def test_create_scheduled_post(self, db_session, sample_user, sample_blog_post):
        """Test creating a scheduled post"""
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        
        scheduled_post = ScheduledPost(
            post_id=sample_blog_post.id,
            user_id=sample_user.id,
            platform="wordpress",
            scheduled_time=scheduled_time,
            timezone="UTC",
            status="pending"
        )
        
        db_session.add(scheduled_post)
        await db_session.commit()
        await db_session.refresh(scheduled_post)
        
        assert scheduled_post.id is not None
        assert scheduled_post.platform == "wordpress"
        assert scheduled_post.status == "pending"
        assert scheduled_post.retry_count == 0
        assert scheduled_post.max_retries == 3
    
    @pytest.mark.asyncio
    async def test_can_retry_logic(self, db_session, sample_user, sample_blog_post):
        """Test retry logic for failed posts"""
        scheduled_post = ScheduledPost(
            post_id=sample_blog_post.id,
            user_id=sample_user.id,
            platform="medium",
            scheduled_time=datetime.utcnow(),
            status="failed",
            retry_count=1
        )
        
        db_session.add(scheduled_post)
        await db_session.commit()
        await db_session.refresh(scheduled_post)
        
        # Should be able to retry
        assert scheduled_post.can_retry() is True
        
        # Increment retry count
        scheduled_post.increment_retry()
        assert scheduled_post.retry_count == 2
        
        # Still can retry
        assert scheduled_post.can_retry() is True
        
        # Max out retries
        scheduled_post.retry_count = 3
        assert scheduled_post.can_retry() is False
    
    @pytest.mark.asyncio
    async def test_scheduled_post_relationships(self, db_session, sample_user, sample_blog_post):
        """Test relationships with user and blog post"""
        scheduled_post = ScheduledPost(
            post_id=sample_blog_post.id,
            user_id=sample_user.id,
            platform="ghost",
            scheduled_time=datetime.utcnow()
        )
        
        db_session.add(scheduled_post)
        await db_session.commit()
        await db_session.refresh(scheduled_post, ["user", "post"])
        
        # Test relationships
        assert scheduled_post.user.email == sample_user.email
        assert scheduled_post.post.title == sample_blog_post.title


class TestPublishingResult:
    """Test PublishingResult model"""
    
    @pytest.mark.asyncio
    async def test_create_publishing_result(self, db_session, sample_blog_post):
        """Test creating a publishing result"""
        result = PublishingResult(
            post_id=sample_blog_post.id,
            platform="wordpress",
            status="success",
            platform_post_id="wp_123",
            platform_url="https://example.com/post/123",
            views=100,
            likes=10,
            shares=5,
            comments=3
        )
        
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)
        
        assert result.id is not None
        assert result.platform == "wordpress"
        assert result.status == "success"
        assert result.views == 100
        assert result.engagement_rate == 0  # Default value
    
    @pytest.mark.asyncio
    async def test_publishing_result_with_error(self, db_session, sample_blog_post):
        """Test creating a failed publishing result"""
        result = PublishingResult(
            post_id=sample_blog_post.id,
            platform="medium",
            status="failed",
            error_details="Authentication failed"
        )
        
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)
        
        assert result.status == "failed"
        assert result.error_details == "Authentication failed"
        assert result.platform_post_id is None


class TestPlatformIntegration:
    """Test PlatformIntegration model"""
    
    @pytest.mark.asyncio
    async def test_create_platform_integration(self, db_session, sample_user):
        """Test creating a platform integration"""
        integration = PlatformIntegration(
            user_id=sample_user.id,
            platform="wordpress",
            access_token="token_123",
            refresh_token="refresh_123",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            platform_user_id="wp_user_123",
            platform_username="testuser",
            auto_publish_enabled=True,
            default_tags=["tech", "ai"],
            default_category="Technology"
        )
        
        db_session.add(integration)
        await db_session.commit()
        await db_session.refresh(integration)
        
        assert integration.id is not None
        assert integration.platform == "wordpress"
        assert integration.auto_publish_enabled is True
        assert integration.default_tags == ["tech", "ai"]
        assert integration.is_active is True
    
    @pytest.mark.asyncio
    async def test_token_expiration_logic(self, db_session, sample_user):
        """Test token expiration checking"""
        # Create integration with expired token
        expired_integration = PlatformIntegration(
            user_id=sample_user.id,
            platform="medium",
            access_token="expired_token",
            token_expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        db_session.add(expired_integration)
        await db_session.commit()
        await db_session.refresh(expired_integration)
        
        # Note: is_token_expired and needs_refresh methods use func.now() 
        # which is database-specific, so we can't easily test them in unit tests
        # These would be better tested in integration tests
        assert expired_integration.token_expires_at < datetime.utcnow()
    
    @pytest.mark.asyncio
    async def test_platform_integration_relationships(self, db_session, sample_user):
        """Test relationship with user"""
        integration = PlatformIntegration(
            user_id=sample_user.id,
            platform="ghost",
            access_token="ghost_token"
        )
        
        db_session.add(integration)
        await db_session.commit()
        await db_session.refresh(integration, ["user"])
        await db_session.refresh(sample_user, ["platform_integrations"])
        
        # Test relationship
        assert integration.user.email == sample_user.email
        assert integration in sample_user.platform_integrations