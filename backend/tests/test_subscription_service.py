"""
Unit tests for subscription service
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.subscription_service import SubscriptionService
from app.models.user import User, SubscriptionPlan
from datetime import datetime
import uuid


class TestSubscriptionService:
    """Test cases for SubscriptionService"""
    
    def test_tier_hierarchy(self):
        """Test subscription tier hierarchy"""
        assert SubscriptionService.TIER_HIERARCHY["free"] == 0
        assert SubscriptionService.TIER_HIERARCHY["basic"] == 1
        assert SubscriptionService.TIER_HIERARCHY["premium"] == 2
    
    def test_subscription_limits(self):
        """Test subscription limits configuration"""
        free_limits = SubscriptionService.SUBSCRIPTION_LIMITS["free"]
        basic_limits = SubscriptionService.SUBSCRIPTION_LIMITS["basic"]
        premium_limits = SubscriptionService.SUBSCRIPTION_LIMITS["premium"]
        
        assert free_limits["posts_limit"] == 5  # From settings
        assert basic_limits["posts_limit"] == 50
        assert premium_limits["posts_limit"] == 500
        
        # Check features
        assert free_limits["features"]["ai_generation"] is True
        assert free_limits["features"]["seo_analysis"] is False
        assert basic_limits["features"]["seo_analysis"] is True
        assert premium_limits["features"]["analytics"] is True
    
    def test_get_subscription_plans(self):
        """Test getting subscription plans"""
        mock_db = Mock(spec=Session)
        
        # Create mock plans
        mock_plans = [
            Mock(spec=SubscriptionPlan, name="free", is_active=True),
            Mock(spec=SubscriptionPlan, name="basic", is_active=True),
            Mock(spec=SubscriptionPlan, name="premium", is_active=True)
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_plans
        
        result = SubscriptionService.get_subscription_plans(mock_db)
        
        assert len(result) == 3
        assert result == mock_plans
    
    def test_get_plan_by_name_success(self):
        """Test getting plan by name successfully"""
        mock_db = Mock(spec=Session)
        
        mock_plan = Mock(spec=SubscriptionPlan, name="basic")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan
        
        result = SubscriptionService.get_plan_by_name(mock_db, "basic")
        
        assert result == mock_plan
    
    def test_get_plan_by_name_not_found(self):
        """Test getting plan by name when not found"""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = SubscriptionService.get_plan_by_name(mock_db, "nonexistent")
        
        assert result is None
    
    def test_can_upgrade_to_plan(self):
        """Test upgrade validation"""
        # Same tier should return False
        assert SubscriptionService.can_upgrade_to_plan("free", "free") is False
        assert SubscriptionService.can_upgrade_to_plan("basic", "basic") is False
        
        # Different tiers should return True (both upgrades and downgrades)
        assert SubscriptionService.can_upgrade_to_plan("free", "basic") is True
        assert SubscriptionService.can_upgrade_to_plan("basic", "premium") is True
        assert SubscriptionService.can_upgrade_to_plan("premium", "basic") is True
        assert SubscriptionService.can_upgrade_to_plan("basic", "free") is True
    
    def test_upgrade_subscription_success(self):
        """Test successful subscription upgrade"""
        mock_db = Mock(spec=Session)
        
        # Create mock user
        mock_user = Mock(spec=User)
        mock_user.subscription_tier = "free"
        mock_user.posts_used_this_month = 2
        
        # Create mock plan
        mock_plan = Mock(spec=SubscriptionPlan)
        mock_plan.name = "basic"
        mock_plan.posts_limit = 50
        mock_plan.price_monthly = 15.00
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan
        
        result = SubscriptionService.upgrade_subscription(
            mock_db, mock_user, "basic", "pm_test123"
        )
        
        assert mock_user.subscription_tier == "basic"
        assert mock_user.posts_limit == 50
        assert mock_user.subscription_status == "active"
        assert result == mock_user
        
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
    
    def test_upgrade_subscription_plan_not_found(self):
        """Test upgrade with non-existent plan"""
        mock_db = Mock(spec=Session)
        mock_user = Mock(spec=User)
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            SubscriptionService.upgrade_subscription(mock_db, mock_user, "nonexistent")
        
        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail
    
    def test_upgrade_subscription_paid_plan_no_payment(self):
        """Test upgrade to paid plan without payment method"""
        mock_db = Mock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.subscription_tier = "free"
        
        mock_plan = Mock(spec=SubscriptionPlan)
        mock_plan.name = "basic"
        mock_plan.price_monthly = 15.00
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan
        
        with pytest.raises(HTTPException) as exc_info:
            SubscriptionService.upgrade_subscription(mock_db, mock_user, "basic")
        
        assert exc_info.value.status_code == 400
        assert "Payment method required" in exc_info.value.detail
    
    def test_upgrade_subscription_downgrade_with_usage_reset(self):
        """Test downgrade that resets usage when over new limit"""
        mock_db = Mock(spec=Session)
        
        mock_user = Mock(spec=User)
        mock_user.subscription_tier = "premium"
        mock_user.posts_used_this_month = 30  # Over basic limit
        
        mock_plan = Mock(spec=SubscriptionPlan)
        mock_plan.name = "basic"
        mock_plan.posts_limit = 50
        mock_plan.price_monthly = 15.00
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_plan
        
        # Mock the tier hierarchy check
        with patch.object(SubscriptionService, 'TIER_HIERARCHY', {"premium": 2, "basic": 1}):
            result = SubscriptionService.upgrade_subscription(
                mock_db, mock_user, "basic", "pm_test123"
            )
        
        assert mock_user.subscription_tier == "basic"
        assert mock_user.posts_limit == 50
        # Usage should not be reset since 30 < 50
        assert mock_user.posts_used_this_month == 30
    
    def test_cancel_subscription(self):
        """Test subscription cancellation"""
        mock_db = Mock(spec=Session)
        mock_user = Mock(spec=User)
        
        with patch.object(SubscriptionService, 'upgrade_subscription') as mock_upgrade:
            mock_upgrade.return_value = mock_user
            
            result = SubscriptionService.cancel_subscription(mock_db, mock_user)
            
            mock_upgrade.assert_called_once_with(mock_db, mock_user, "free")
            assert result == mock_user
    
    def test_track_post_usage_success(self):
        """Test successful post usage tracking"""
        mock_db = Mock(spec=Session)
        
        mock_user = Mock(spec=User)
        mock_user.can_create_post.return_value = True
        
        result = SubscriptionService.track_post_usage(mock_db, mock_user)
        
        mock_user.increment_post_usage.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
        assert result == mock_user
    
    def test_track_post_usage_limit_exceeded(self):
        """Test post usage tracking when limit exceeded"""
        mock_db = Mock(spec=Session)
        
        mock_user = Mock(spec=User)
        mock_user.can_create_post.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            SubscriptionService.track_post_usage(mock_db, mock_user)
        
        assert exc_info.value.status_code == 403
        assert "limit exceeded" in exc_info.value.detail
    
    def test_reset_monthly_usage(self):
        """Test monthly usage reset"""
        mock_db = Mock(spec=Session)
        
        mock_user = Mock(spec=User)
        
        result = SubscriptionService.reset_monthly_usage(mock_db, mock_user)
        
        mock_user.reset_monthly_usage.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
        assert result == mock_user
    
    def test_get_usage_stats(self):
        """Test getting usage statistics"""
        mock_user = Mock(spec=User)
        mock_user.posts_used_this_month = 15
        mock_user.posts_limit = 50
        mock_user.subscription_tier = "basic"
        mock_user.subscription_status = "active"
        
        with patch('app.services.subscription_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 1, 15)
            mock_datetime.return_value = datetime(2025, 1, 15)
            
            result = SubscriptionService.get_usage_stats(mock_user)
        
        assert result["posts_used_this_month"] == 15
        assert result["posts_limit"] == 50
        assert result["posts_remaining"] == 35
        assert result["usage_percentage"] == 30.0
        assert result["subscription_tier"] == "basic"
        assert result["subscription_status"] == "active"
    
    def test_get_plan_features(self):
        """Test getting plan features"""
        free_features = SubscriptionService.get_plan_features("free")
        basic_features = SubscriptionService.get_plan_features("basic")
        premium_features = SubscriptionService.get_plan_features("premium")
        
        assert free_features["ai_generation"] is True
        assert free_features["seo_analysis"] is False
        
        assert basic_features["seo_analysis"] is True
        assert basic_features["scheduling"] is True
        
        assert premium_features["analytics"] is True
        assert premium_features["priority_support"] is True
    
    def test_user_has_feature(self):
        """Test checking if user has specific feature"""
        mock_user = Mock(spec=User)
        mock_user.subscription_tier = "basic"
        
        # Basic plan should have SEO analysis
        assert SubscriptionService.user_has_feature(mock_user, "seo_analysis") is True
        
        # Basic plan should not have analytics
        assert SubscriptionService.user_has_feature(mock_user, "analytics") is False
        
        # Non-existent feature should return False
        assert SubscriptionService.user_has_feature(mock_user, "nonexistent_feature") is False
    
    def test_get_billing_info(self):
        """Test getting billing information"""
        mock_user = Mock(spec=User)
        mock_user.subscription_tier = "basic"
        mock_user.subscription_status = "active"
        
        with patch('app.services.subscription_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 1, 15)
            mock_datetime.return_value = datetime(2025, 1, 15)
            
            result = SubscriptionService.get_billing_info(mock_user)
        
        assert result["subscription_tier"] == "basic"
        assert result["subscription_status"] == "active"
        assert result["amount_due"] == 15.00
        assert result["payment_method"] == "****1234"
        assert result["current_period_start"] is not None
        assert result["next_billing_date"] is not None
    
    def test_get_billing_info_free_plan(self):
        """Test getting billing info for free plan"""
        mock_user = Mock(spec=User)
        mock_user.subscription_tier = "free"
        mock_user.subscription_status = "active"
        
        result = SubscriptionService.get_billing_info(mock_user)
        
        assert result["subscription_tier"] == "free"
        assert result["amount_due"] is None
        assert result["payment_method"] is None
        assert result["current_period_start"] is None
        assert result["next_billing_date"] is None
    
    def test_create_default_plans(self):
        """Test creating default subscription plans"""
        mock_db = Mock(spec=Session)
        
        # Mock that no plans exist
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        SubscriptionService.create_default_plans(mock_db)
        
        # Should add 3 plans (free, basic, premium)
        assert mock_db.add.call_count == 3
        mock_db.commit.assert_called_once()
    
    def test_create_default_plans_already_exist(self):
        """Test creating default plans when they already exist"""
        mock_db = Mock(spec=Session)
        
        # Mock that plans already exist
        mock_existing_plan = Mock(spec=SubscriptionPlan)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_plan
        
        SubscriptionService.create_default_plans(mock_db)
        
        # Should not add any plans
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()