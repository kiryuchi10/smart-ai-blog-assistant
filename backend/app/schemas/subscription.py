"""
Pydantic schemas for subscription management
"""
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class SubscriptionPlanResponse(BaseModel):
    """Schema for subscription plan response"""
    id: str
    name: str
    price_monthly: Optional[Decimal]
    posts_limit: int
    features: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionUpgradeRequest(BaseModel):
    """Schema for subscription upgrade request"""
    plan_name: str
    
    @field_validator('plan_name')
    @classmethod
    def validate_plan_name(cls, v):
        allowed_plans = ['free', 'basic', 'premium']
        if v not in allowed_plans:
            raise ValueError(f'Plan must be one of: {", ".join(allowed_plans)}')
        return v


class UsageResponse(BaseModel):
    """Schema for usage tracking response"""
    posts_used_this_month: int
    posts_limit: int
    posts_remaining: int
    usage_percentage: float
    reset_date: datetime
    
    @classmethod
    def from_user(cls, user):
        """Create usage response from user model"""
        posts_remaining = max(0, user.posts_limit - user.posts_used_this_month)
        usage_percentage = (user.posts_used_this_month / user.posts_limit) * 100 if user.posts_limit > 0 else 0
        
        # Calculate next reset date (first day of next month)
        from datetime import datetime, timedelta
        import calendar
        
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)
        
        return cls(
            posts_used_this_month=user.posts_used_this_month,
            posts_limit=user.posts_limit,
            posts_remaining=posts_remaining,
            usage_percentage=round(usage_percentage, 2),
            reset_date=reset_date
        )


class BillingInfoResponse(BaseModel):
    """Schema for billing information response"""
    subscription_tier: str
    subscription_status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    next_billing_date: Optional[datetime]
    amount_due: Optional[Decimal]
    payment_method: Optional[str]
    
    class Config:
        from_attributes = True


class SubscriptionHistoryItem(BaseModel):
    """Schema for subscription history item"""
    date: datetime
    action: str  # upgrade, downgrade, cancel, reactivate
    from_plan: Optional[str]
    to_plan: Optional[str]
    amount: Optional[Decimal]
    
    class Config:
        from_attributes = True


class SubscriptionHistoryResponse(BaseModel):
    """Schema for subscription history response"""
    items: list[SubscriptionHistoryItem]
    total_count: int


class StripePaymentIntentRequest(BaseModel):
    """Schema for Stripe payment intent creation"""
    plan_name: str
    payment_method_id: Optional[str] = None
    
    @field_validator('plan_name')
    @classmethod
    def validate_plan_name(cls, v):
        allowed_plans = ['basic', 'premium']  # Free doesn't require payment
        if v not in allowed_plans:
            raise ValueError(f'Plan must be one of: {", ".join(allowed_plans)}')
        return v


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent response"""
    client_secret: str
    amount: int  # Amount in cents
    currency: str
    plan_name: str


class WebhookEventResponse(BaseModel):
    """Schema for webhook event response"""
    received: bool = True
    message: str = "Webhook received successfully"