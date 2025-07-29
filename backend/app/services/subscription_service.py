"""
Subscription management service
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, SubscriptionPlan
from app.core.config import settings
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import calendar


class SubscriptionService:
    """Service for managing user subscriptions"""
    
    # Subscription tier hierarchy for upgrades/downgrades
    TIER_HIERARCHY = {
        "free": 0,
        "basic": 1,
        "premium": 2
    }
    
    # Default subscription limits
    SUBSCRIPTION_LIMITS = {
        "free": {
            "posts_limit": settings.free_tier_post_limit,
            "features": {
                "ai_generation": True,
                "basic_templates": True,
                "seo_analysis": False,
                "scheduling": False,
                "analytics": False,
                "priority_support": False
            }
        },
        "basic": {
            "posts_limit": settings.basic_tier_post_limit,
            "features": {
                "ai_generation": True,
                "basic_templates": True,
                "premium_templates": True,
                "seo_analysis": True,
                "scheduling": True,
                "analytics": False,
                "priority_support": False
            }
        },
        "premium": {
            "posts_limit": settings.premium_tier_post_limit,
            "features": {
                "ai_generation": True,
                "basic_templates": True,
                "premium_templates": True,
                "seo_analysis": True,
                "scheduling": True,
                "analytics": True,
                "priority_support": True,
                "custom_templates": True,
                "bulk_operations": True
            }
        }
    }
    
    @staticmethod
    def get_subscription_plans(db: Session) -> list[SubscriptionPlan]:
        """Get all active subscription plans"""
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()
    
    @staticmethod
    def get_plan_by_name(db: Session, plan_name: str) -> Optional[SubscriptionPlan]:
        """Get subscription plan by name"""
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.name == plan_name,
            SubscriptionPlan.is_active == True
        ).first()
    
    @staticmethod
    def can_upgrade_to_plan(current_tier: str, target_tier: str) -> bool:
        """Check if user can upgrade to target tier"""
        current_level = SubscriptionService.TIER_HIERARCHY.get(current_tier, 0)
        target_level = SubscriptionService.TIER_HIERARCHY.get(target_tier, 0)
        return target_level != current_level  # Allow both upgrades and downgrades
    
    @staticmethod
    def upgrade_subscription(
        db: Session, 
        user: User, 
        new_plan_name: str,
        payment_method_id: Optional[str] = None
    ) -> User:
        """Upgrade user subscription to new plan"""
        
        # Validate plan exists
        new_plan = SubscriptionService.get_plan_by_name(db, new_plan_name)
        if not new_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription plan '{new_plan_name}' not found"
            )
        
        # Check if upgrade is allowed
        if not SubscriptionService.can_upgrade_to_plan(user.subscription_tier, new_plan_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change from {user.subscription_tier} to {new_plan_name}"
            )
        
        # For paid plans, validate payment method (in production, integrate with Stripe)
        if new_plan_name != "free" and new_plan.price_monthly and new_plan.price_monthly > 0:
            if not payment_method_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment method required for paid plans"
                )
            
            # TODO: Process payment with Stripe
            # This would involve creating a subscription in Stripe
            # For now, we'll just simulate successful payment
        
        # Update user subscription
        old_tier = user.subscription_tier
        user.subscription_tier = new_plan_name
        user.posts_limit = new_plan.posts_limit
        user.subscription_status = "active"
        
        # If downgrading and user has exceeded new limit, reset usage
        if (SubscriptionService.TIER_HIERARCHY.get(new_plan_name, 0) < 
            SubscriptionService.TIER_HIERARCHY.get(old_tier, 0)):
            if user.posts_used_this_month > new_plan.posts_limit:
                user.posts_used_this_month = new_plan.posts_limit
        
        db.commit()
        db.refresh(user)
        
        # TODO: Log subscription change for billing history
        # TODO: Send confirmation email
        
        return user
    
    @staticmethod
    def cancel_subscription(db: Session, user: User) -> User:
        """Cancel user subscription (downgrade to free)"""
        return SubscriptionService.upgrade_subscription(db, user, "free")
    
    @staticmethod
    def track_post_usage(db: Session, user: User) -> User:
        """Increment user's post usage counter"""
        if not user.can_create_post():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Monthly post limit exceeded"
            )
        
        user.increment_post_usage()
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def reset_monthly_usage(db: Session, user: User) -> User:
        """Reset user's monthly post usage (called by scheduled job)"""
        user.reset_monthly_usage()
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_usage_stats(user: User) -> Dict[str, Any]:
        """Get user's usage statistics"""
        posts_remaining = max(0, user.posts_limit - user.posts_used_this_month)
        usage_percentage = (user.posts_used_this_month / user.posts_limit) * 100 if user.posts_limit > 0 else 0
        
        # Calculate next reset date (first day of next month)
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)
        
        return {
            "posts_used_this_month": user.posts_used_this_month,
            "posts_limit": user.posts_limit,
            "posts_remaining": posts_remaining,
            "usage_percentage": round(usage_percentage, 2),
            "reset_date": reset_date,
            "subscription_tier": user.subscription_tier,
            "subscription_status": user.subscription_status
        }
    
    @staticmethod
    def get_plan_features(plan_name: str) -> Dict[str, Any]:
        """Get features for a subscription plan"""
        return SubscriptionService.SUBSCRIPTION_LIMITS.get(plan_name, {}).get("features", {})
    
    @staticmethod
    def user_has_feature(user: User, feature_name: str) -> bool:
        """Check if user has access to a specific feature"""
        plan_features = SubscriptionService.get_plan_features(user.subscription_tier)
        return plan_features.get(feature_name, False)
    
    @staticmethod
    def get_billing_info(user: User) -> Dict[str, Any]:
        """Get user's billing information"""
        # In production, this would fetch from Stripe
        # For now, return mock data
        
        now = datetime.utcnow()
        
        # Calculate billing period (monthly)
        period_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1) - timedelta(days=1)
            next_billing = datetime(now.year + 1, 1, 1)
        else:
            period_end = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
            next_billing = datetime(now.year, now.month + 1, 1)
        
        # Get plan pricing
        amount_due = None
        if user.subscription_tier == "basic":
            amount_due = 15.00  # $15/month
        elif user.subscription_tier == "premium":
            amount_due = 29.00  # $29/month
        
        return {
            "subscription_tier": user.subscription_tier,
            "subscription_status": user.subscription_status,
            "current_period_start": period_start if user.subscription_tier != "free" else None,
            "current_period_end": period_end if user.subscription_tier != "free" else None,
            "next_billing_date": next_billing if user.subscription_tier != "free" else None,
            "amount_due": amount_due,
            "payment_method": "****1234" if user.subscription_tier != "free" else None  # Mock payment method
        }
    
    @staticmethod
    def create_default_plans(db: Session):
        """Create default subscription plans if they don't exist"""
        plans_data = [
            {
                "name": "free",
                "price_monthly": None,
                "posts_limit": settings.free_tier_post_limit,
                "features": SubscriptionService.SUBSCRIPTION_LIMITS["free"]["features"]
            },
            {
                "name": "basic",
                "price_monthly": 15.00,
                "posts_limit": settings.basic_tier_post_limit,
                "features": SubscriptionService.SUBSCRIPTION_LIMITS["basic"]["features"]
            },
            {
                "name": "premium",
                "price_monthly": 29.00,
                "posts_limit": settings.premium_tier_post_limit,
                "features": SubscriptionService.SUBSCRIPTION_LIMITS["premium"]["features"]
            }
        ]
        
        for plan_data in plans_data:
            existing_plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.name == plan_data["name"]
            ).first()
            
            if not existing_plan:
                plan = SubscriptionPlan(
                    name=plan_data["name"],
                    price_monthly=plan_data["price_monthly"],
                    posts_limit=plan_data["posts_limit"],
                    features=plan_data["features"],
                    is_active=True
                )
                db.add(plan)
        
        db.commit()


# Utility functions for feature checking
def require_feature(feature_name: str):
    """Decorator to require specific subscription feature"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be used as a dependency in FastAPI routes
            # For now, it's just a placeholder
            return func(*args, **kwargs)
        return wrapper
    return decorator


async def check_usage_limits(user: User, db: Session):
    """Check if user can create more content based on subscription limits"""
    if not user.can_create_post():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Monthly post limit exceeded. Used {user.posts_used_this_month}/{user.posts_limit} posts."
        )