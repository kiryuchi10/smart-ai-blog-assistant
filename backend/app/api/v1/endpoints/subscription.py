"""
Subscription management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth_middleware import get_current_active_user
from app.services.subscription_service import SubscriptionService
from app.services.rate_limiter import rate_limit_auth
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionPlanResponse,
    SubscriptionUpgradeRequest,
    UsageResponse,
    BillingInfoResponse,
    StripePaymentIntentRequest,
    PaymentIntentResponse,
    WebhookEventResponse
)
from app.schemas.auth import MessageResponse
from typing import List
import secrets

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(db: Session = Depends(get_db)):
    """
    Get all available subscription plans
    """
    plans = SubscriptionService.get_subscription_plans(db)
    return [SubscriptionPlanResponse.from_orm(plan) for plan in plans]


@router.get("/usage", response_model=UsageResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's usage statistics
    """
    return UsageResponse.from_user(current_user)


@router.get("/billing", response_model=BillingInfoResponse)
async def get_billing_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's billing information
    """
    billing_info = SubscriptionService.get_billing_info(current_user)
    return BillingInfoResponse(**billing_info)


@router.post("/upgrade", response_model=MessageResponse)
async def upgrade_subscription(
    upgrade_request: SubscriptionUpgradeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upgrade user subscription to a new plan
    """
    # Apply rate limiting
    rate_limit_auth(request)
    
    # Check if user is already on this plan
    if current_user.subscription_tier == upgrade_request.plan_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already subscribed to {upgrade_request.plan_name} plan"
        )
    
    # Upgrade subscription
    updated_user = SubscriptionService.upgrade_subscription(
        db, current_user, upgrade_request.plan_name
    )
    
    return MessageResponse(
        message=f"Successfully upgraded to {upgrade_request.plan_name} plan"
    )


@router.post("/downgrade", response_model=MessageResponse)
async def downgrade_subscription(
    downgrade_request: SubscriptionUpgradeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Downgrade user subscription to a lower plan
    """
    # Apply rate limiting
    rate_limit_auth(request)
    
    # Check if user is already on this plan
    if current_user.subscription_tier == downgrade_request.plan_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already subscribed to {downgrade_request.plan_name} plan"
        )
    
    # Check if this is actually a downgrade
    current_level = SubscriptionService.TIER_HIERARCHY.get(current_user.subscription_tier, 0)
    target_level = SubscriptionService.TIER_HIERARCHY.get(downgrade_request.plan_name, 0)
    
    if target_level > current_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /upgrade endpoint for upgrading subscription"
        )
    
    # Downgrade subscription
    updated_user = SubscriptionService.upgrade_subscription(
        db, current_user, downgrade_request.plan_name
    )
    
    return MessageResponse(
        message=f"Successfully downgraded to {downgrade_request.plan_name} plan"
    )


@router.post("/cancel", response_model=MessageResponse)
async def cancel_subscription(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel user subscription (downgrade to free plan)
    """
    # Apply rate limiting
    rate_limit_auth(request)
    
    if current_user.subscription_tier == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already on free plan"
        )
    
    # Cancel subscription
    updated_user = SubscriptionService.cancel_subscription(db, current_user)
    
    return MessageResponse(message="Subscription cancelled successfully")


@router.post("/track-usage", response_model=MessageResponse)
async def track_post_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Track post usage (increment counter)
    This endpoint would be called when a user creates a post
    """
    updated_user = SubscriptionService.track_post_usage(db, current_user)
    
    posts_remaining = updated_user.posts_limit - updated_user.posts_used_this_month
    
    return MessageResponse(
        message=f"Post usage tracked. {posts_remaining} posts remaining this month."
    )


@router.get("/features/{feature_name}")
async def check_feature_access(
    feature_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Check if user has access to a specific feature
    """
    has_access = SubscriptionService.user_has_feature(current_user, feature_name)
    
    return {
        "feature": feature_name,
        "has_access": has_access,
        "subscription_tier": current_user.subscription_tier
    }


@router.get("/features")
async def get_user_features(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all features available to the current user
    """
    features = SubscriptionService.get_plan_features(current_user.subscription_tier)
    
    return {
        "subscription_tier": current_user.subscription_tier,
        "features": features
    }


# Stripe integration endpoints (placeholder for future implementation)
@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_request: StripePaymentIntentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create Stripe payment intent for subscription upgrade
    """
    # Get plan details
    plan = SubscriptionService.get_plan_by_name(db, payment_request.plan_name)
    if not plan or not plan.price_monthly:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan or plan is free"
        )
    
    # In production, this would create a Stripe PaymentIntent
    # For now, return mock data
    mock_client_secret = f"pi_{secrets.token_urlsafe(16)}_secret_{secrets.token_urlsafe(16)}"
    
    return PaymentIntentResponse(
        client_secret=mock_client_secret,
        amount=int(plan.price_monthly * 100),  # Convert to cents
        currency="usd",
        plan_name=plan.name
    )


@router.post("/webhook/stripe", response_model=WebhookEventResponse)
async def handle_stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events
    """
    # In production, this would:
    # 1. Verify webhook signature
    # 2. Parse webhook event
    # 3. Update user subscription based on event type
    # 4. Handle failed payments, subscription updates, etc.
    
    # For now, just return success
    return WebhookEventResponse(
        received=True,
        message="Webhook processed successfully"
    )


@router.post("/reset-usage", response_model=MessageResponse)
async def reset_monthly_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reset monthly usage counter (admin/testing endpoint)
    In production, this would be called by a scheduled job
    """
    updated_user = SubscriptionService.reset_monthly_usage(db, current_user)
    
    return MessageResponse(message="Monthly usage reset successfully")


@router.post("/initialize-plans", response_model=MessageResponse)
async def initialize_subscription_plans(
    db: Session = Depends(get_db)
):
    """
    Initialize default subscription plans (admin endpoint)
    """
    SubscriptionService.create_default_plans(db)
    
    return MessageResponse(message="Default subscription plans created successfully")