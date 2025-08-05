"""
Unit tests for user model validation and subscription logic
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.models.user import User, SubscriptionPlan


class TestSubscriptionPlan:
    """Test cases for SubscriptionPlan model"""
    
    @pytest.mark.asyncio
    async def test_create_subscription_plan(self, db_session):
        """Test creating a subscription plan"""
        plan = SubscriptionPlan(
            name="Premium Plan",
            description="Premium features for power users",
            price_monthly=49.99,
            price_yearly=499.99,
            posts_limit=500,
            api_calls_limit=5000,
            storage_limit_gb=50,
            folder_monitoring=True,
            comment_analysis=True,
            advanced_analytics=True,
            priority_support=True,
            multi_platform_publishing=True,
            ai_content_enhancement=True,
            api_data_integration=True,
            custom_templates=True,
            bulk_operations=True,
            white_label=False,
            trial_days=14,
            is_active=True,
            sort_order=2,
        )
        
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        
        assert plan.id is not None
        assert plan.name == "Premium Plan"
        assert plan.price_monthly == 49.99
        assert plan.posts_limit == 500
        assert plan.folder_monitoring is True
        assert plan.is_active is True
    
    @pytest.mark.asyncio
    async def test_subscription_plan_yearly_discount(self, sample_subscription_plan):
        """Test yearly discount calculation"""
        discount = sample_subscription_plan.yearly_discount_percentage
        expected_discount = round(((29.99 * 12 - 299.99) / (29.99 * 12)) * 100, 1)
        assert discount == expected_discount
    
    @pytest.mark.asyncio
    async def test_subscription_plan_has_feature(self, sample_subscription_plan):
        """Test feature checking"""
        assert sample_subscription_plan.has_feature("folder_monitoring") is True
        assert sample_subscription_plan.has_feature("comment_analysis") is True
        assert sample_subscription_plan.has_feature("advanced_analytics") is False
        assert sample_subscription_plan.has_feature("white_label") is False
    
    @pytest.mark.asyncio
    async def test_subscription_plan_get_feature_config(self, db_session):
        """Test getting feature configuration"""
        plan = SubscriptionPlan(
            name="Custom Plan",
            posts_limit=100,
            api_calls_limit=1000,
            features={
                "custom_feature": {"enabled": True, "limit": 50},
                "another_feature": {"enabled": False}
            }
        )
        
        db_session.add(plan)
        await db_session.commit()
        
        config = plan.get_feature_config("custom_feature")
        assert config == {"enabled": True, "limit": 50}
        
        empty_config = plan.get_feature_config("nonexistent_feature")
        assert empty_config == {}
    
    def test_subscription_plan_class_methods(self):
        """Test class methods for default plans"""
        free_plan = SubscriptionPlan.get_free_plan()
        assert free_plan["name"] == "Free"
        assert free_plan["price_monthly"] == 0
        assert free_plan["posts_limit"] == 5
        assert free_plan["folder_monitoring"] is False
        
        starter_plan = SubscriptionPlan.get_starter_plan()
        assert starter_plan["name"] == "Starter"
        assert starter_plan["price_monthly"] == 19.99
        assert starter_plan["posts_limit"] == 50
        assert starter_plan["folder_monitoring"] is True
        
        professional_plan = SubscriptionPlan.get_professional_plan()
        assert professional_plan["name"] == "Professional"
        assert professional_plan["price_monthly"] == 49.99
        assert professional_plan["posts_limit"] == 200
        assert professional_plan["advanced_analytics"] is True
        
        enterprise_plan = SubscriptionPlan.get_enterprise_plan()
        assert enterprise_plan["name"] == "Enterprise"
        assert enterprise_plan["price_monthly"] == 199.99
        assert enterprise_plan["posts_limit"] == 1000
        assert enterprise_plan["white_label"] is True


class TestUser:
    """Test cases for User model"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session, sample_subscription_plan):
        """Test creating a user"""
        user = User(
            email="newuser@example.com",
            password_hash="hashed_password_123",
            first_name="New",
            last_name="User",
            subscription_tier="professional",
            subscription_plan_id=sample_subscription_plan.id,
            posts_limit=200,
            api_calls_limit=2000,
            folder_monitoring_enabled=True,
            comment_analysis_enabled=True,
            advanced_analytics_enabled=True,
            preferred_platforms=["wordpress", "medium", "ghost"],
            default_content_tone="casual",
            default_content_length="long",
            timezone="America/New_York",
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.subscription_tier == "professional"
        assert user.posts_limit == 200
        assert user.folder_monitoring_enabled is True
        assert user.preferred_platforms == ["wordpress", "medium", "ghost"]
        assert user.timezone == "America/New_York"
    
    @pytest.mark.asyncio
    async def test_user_full_name_property(self, sample_user):
        """Test full name property"""
        assert sample_user.full_name == "Test User"
        
        # Test with only first name
        sample_user.last_name = None
        assert sample_user.full_name == "Test"
        
        # Test with only last name
        sample_user.first_name = None
        sample_user.last_name = "User"
        assert sample_user.full_name == "User"
        
        # Test with no names (should return email prefix)
        sample_user.first_name = None
        sample_user.last_name = None
        assert sample_user.full_name == "test"
    
    @pytest.mark.asyncio
    async def test_user_usage_properties(self, sample_user):
        """Test usage tracking properties"""
        # Test posts remaining
        sample_user.posts_used_this_month = 30
        sample_user.posts_limit = 100
        assert sample_user.posts_remaining == 70
        
        # Test when usage exceeds limit
        sample_user.posts_used_this_month = 120
        assert sample_user.posts_remaining == 0
        
        # Test API calls remaining
        sample_user.api_calls_used_this_month = 500
        sample_user.api_calls_limit = 1000
        assert sample_user.api_calls_remaining == 500
        
        # Test when API usage exceeds limit
        sample_user.api_calls_used_this_month = 1200
        assert sample_user.api_calls_remaining == 0
    
    @pytest.mark.asyncio
    async def test_user_subscription_status(self, sample_user):
        """Test subscription status checking"""
        # Test active subscription
        sample_user.subscription_status = "active"
        sample_user.subscription_ends_at = datetime.utcnow() + timedelta(days=30)
        assert sample_user.is_subscription_active is True
        
        # Test expired subscription
        sample_user.subscription_ends_at = datetime.utcnow() - timedelta(days=1)
        assert sample_user.is_subscription_active is False
        
        # Test inactive subscription
        sample_user.subscription_status = "cancelled"
        sample_user.subscription_ends_at = datetime.utcnow() + timedelta(days=30)
        assert sample_user.is_subscription_active is False
    
    @pytest.mark.asyncio
    async def test_user_trial_status(self, sample_user):
        """Test trial status checking"""
        # Test active trial
        sample_user.trial_ends_at = datetime.utcnow() + timedelta(days=7)
        assert sample_user.is_trial_active is True
        
        # Test expired trial
        sample_user.trial_ends_at = datetime.utcnow() - timedelta(days=1)
        assert sample_user.is_trial_active is False
        
        # Test no trial
        sample_user.trial_ends_at = None
        assert sample_user.is_trial_active is False
    
    @pytest.mark.asyncio
    async def test_user_feature_access(self, sample_user):
        """Test feature access checking"""
        sample_user.folder_monitoring_enabled = True
        sample_user.comment_analysis_enabled = True
        sample_user.advanced_analytics_enabled = False
        sample_user.priority_support_enabled = False
        
        assert sample_user.can_use_feature("folder_monitoring") is True
        assert sample_user.can_use_feature("comment_analysis") is True
        assert sample_user.can_use_feature("advanced_analytics") is False
        assert sample_user.can_use_feature("priority_support") is False
        assert sample_user.can_use_feature("nonexistent_feature") is False
    
    @pytest.mark.asyncio
    async def test_user_usage_increment(self, sample_user, db_session):
        """Test usage increment methods"""
        initial_posts = sample_user.posts_used_this_month
        initial_api_calls = sample_user.api_calls_used_this_month
        
        # Test increment posts
        sample_user.increment_posts_used()
        assert sample_user.posts_used_this_month == initial_posts + 1
        
        # Test increment API calls
        sample_user.increment_api_calls_used(5)
        assert sample_user.api_calls_used_this_month == initial_api_calls + 5
        
        # Test default API calls increment
        sample_user.increment_api_calls_used()
        assert sample_user.api_calls_used_this_month == initial_api_calls + 6
    
    @pytest.mark.asyncio
    async def test_user_usage_reset(self, sample_user):
        """Test monthly usage reset"""
        sample_user.posts_used_this_month = 50
        sample_user.api_calls_used_this_month = 500
        old_reset_time = sample_user.usage_reset_at
        
        sample_user.reset_monthly_usage()
        
        assert sample_user.posts_used_this_month == 0
        assert sample_user.api_calls_used_this_month == 0
        assert sample_user.usage_reset_at > old_reset_time
    
    @pytest.mark.asyncio
    async def test_user_unique_constraints(self, db_session, sample_subscription_plan):
        """Test unique constraints on user fields"""
        # Test unique email constraint
        user1 = User(
            email="unique@example.com",
            password_hash="hash1",
            subscription_plan_id=sample_subscription_plan.id,
        )
        
        user2 = User(
            email="unique@example.com",  # Same email
            password_hash="hash2",
            subscription_plan_id=sample_subscription_plan.id,
        )
        
        db_session.add(user1)
        await db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_user_relationship_with_subscription_plan(self, db_session, sample_user, sample_subscription_plan):
        """Test relationship between user and subscription plan"""
        # Refresh to load relationships
        await db_session.refresh(sample_user, ["subscription_plan"])
        
        assert sample_user.subscription_plan is not None
        assert sample_user.subscription_plan.id == sample_subscription_plan.id
        assert sample_user.subscription_plan.name == sample_subscription_plan.name
    
    @pytest.mark.asyncio
    async def test_user_to_dict_method(self, sample_user):
        """Test converting user to dictionary"""
        user_dict = sample_user.to_dict()
        
        assert isinstance(user_dict, dict)
        assert "id" in user_dict
        assert "email" in user_dict
        assert "created_at" in user_dict
        assert "updated_at" in user_dict
        assert user_dict["email"] == sample_user.email
        assert user_dict["subscription_tier"] == sample_user.subscription_tier
    
    @pytest.mark.asyncio
    async def test_user_repr_method(self, sample_user):
        """Test user string representation"""
        repr_str = repr(sample_user)
        
        assert "User" in repr_str
        assert str(sample_user.id) in repr_str
        assert sample_user.email in repr_str
        assert sample_user.subscription_tier in repr_str


class TestUserSubscriptionIntegration:
    """Test cases for user and subscription plan integration"""
    
    @pytest.mark.asyncio
    async def test_user_subscription_plan_relationship(self, db_session):
        """Test the relationship between users and subscription plans"""
        # Create a subscription plan
        plan = SubscriptionPlan(
            name="Integration Test Plan",
            posts_limit=100,
            api_calls_limit=1000,
            folder_monitoring=True,
            comment_analysis=True,
        )
        
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        
        # Create users with this plan
        user1 = User(
            email="user1@example.com",
            password_hash="hash1",
            subscription_plan_id=plan.id,
        )
        
        user2 = User(
            email="user2@example.com",
            password_hash="hash2",
            subscription_plan_id=plan.id,
        )
        
        db_session.add_all([user1, user2])
        await db_session.commit()
        
        # Test relationship from plan to users
        await db_session.refresh(plan, ["users"])
        assert len(plan.users) == 2
        assert user1 in plan.users
        assert user2 in plan.users
        
        # Test relationship from user to plan
        await db_session.refresh(user1, ["subscription_plan"])
        assert user1.subscription_plan == plan
    
    @pytest.mark.asyncio
    async def test_subscription_plan_deletion_with_users(self, db_session):
        """Test what happens when a subscription plan with users is deleted"""
        # Create a subscription plan
        plan = SubscriptionPlan(
            name="To Be Deleted Plan",
            posts_limit=50,
            api_calls_limit=500,
        )
        
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        
        # Create a user with this plan
        user = User(
            email="orphan@example.com",
            password_hash="hash",
            subscription_plan_id=plan.id,
        )
        
        db_session.add(user)
        await db_session.commit()
        
        # Delete the plan (should set user's subscription_plan_id to NULL due to FK constraint)
        await db_session.delete(plan)
        await db_session.commit()
        
        # Refresh user and check that subscription_plan_id is None
        await db_session.refresh(user)
        assert user.subscription_plan_id is None