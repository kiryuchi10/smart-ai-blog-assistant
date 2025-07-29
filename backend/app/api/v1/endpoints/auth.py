"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.services.auth_service import AuthService
from app.services.rate_limiter import rate_limit_auth, rate_limit_password_reset
from app.models.user import User
from app.schemas.auth import (
    UserRegistration, 
    UserLogin, 
    TokenResponse, 
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserResponse,
    MessageResponse,
    ErrorResponse
)
from app.core.config import settings
import secrets
import uuid

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistration,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account
    """
    # Apply rate limiting
    rate_limit_auth(request)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = AuthService.hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        subscription_tier="free",
        subscription_status="active",
        posts_limit=settings.free_tier_post_limit,
        is_active=True,
        is_verified=False  # Email verification required
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate tokens
    access_token = AuthService.create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )
    refresh_token = AuthService.create_refresh_token(str(new_user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_expiration_hours * 3600
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access tokens
    """
    # Apply rate limiting
    rate_limit_auth(request)
    
    # Authenticate user
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate tokens
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = AuthService.create_refresh_token(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_expiration_hours * 3600
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    request: Request
):
    """
    Refresh access token using refresh token
    """
    # Apply rate limiting
    rate_limit_auth(request)
    
    try:
        new_access_token = AuthService.refresh_access_token(refresh_data.refresh_token)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_data.refresh_token,  # Keep same refresh token
            expires_in=settings.jwt_expiration_hours * 3600
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user by revoking tokens
    """
    # Get token from authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    # Blacklist the access token
    payload = AuthService.verify_token(token)
    expires_at = datetime.fromtimestamp(payload["exp"])
    AuthService.blacklist_token(token, expires_at)
    
    # Revoke refresh token
    AuthService.revoke_refresh_token(str(current_user.id))
    
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)


@router.post("/password-reset", response_model=MessageResponse)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request password reset email
    """
    # Apply rate limiting
    rate_limit_password_reset(request)
    
    # Check if user exists
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    # Always return success to prevent email enumeration
    if user:
        # Generate reset token (in production, send via email)
        reset_token = secrets.token_urlsafe(32)
        
        # Store reset token in Redis with 1 hour expiration
        from app.services.auth_service import redis_client
        redis_client.setex(
            f"password_reset:{reset_token}",
            3600,  # 1 hour
            str(user.id)
        )
        
        # TODO: Send email with reset token
        # For now, we'll just log it (remove in production)
        print(f"Password reset token for {user.email}: {reset_token}")
    
    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with token
    """
    # Apply rate limiting
    rate_limit_password_reset(request)
    
    # Verify reset token
    from app.services.auth_service import redis_client
    user_id = redis_client.get(f"password_reset:{reset_data.token}")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = AuthService.hash_password(reset_data.new_password)
    db.commit()
    
    # Delete reset token
    redis_client.delete(f"password_reset:{reset_data.token}")
    
    # Revoke all existing tokens for security
    AuthService.revoke_refresh_token(str(user.id))
    
    return MessageResponse(message="Password successfully reset")


@router.post("/verify-email/{token}", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user email with token
    """
    # Verify email token (simplified - in production use proper JWT or signed tokens)
    from app.services.auth_service import redis_client
    user_id = redis_client.get(f"email_verify:{token}")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Get user and mark as verified
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    user.is_verified = True
    db.commit()
    
    # Delete verification token
    redis_client.delete(f"email_verify:{token}")
    
    return MessageResponse(message="Email successfully verified")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    current_user: User = Depends(get_current_user)
):
    """
    Resend email verification
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate verification token
    verify_token = secrets.token_urlsafe(32)
    
    # Store verification token in Redis with 24 hour expiration
    from app.services.auth_service import redis_client
    redis_client.setex(
        f"email_verify:{verify_token}",
        86400,  # 24 hours
        str(current_user.id)
    )
    
    # TODO: Send verification email
    # For now, we'll just log it (remove in production)
    print(f"Email verification token for {current_user.email}: {verify_token}")
    
    return MessageResponse(message="Verification email sent")