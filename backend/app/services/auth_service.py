"""
JWT Authentication service for user authentication and token management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
import redis
import json

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis client for token blacklisting and refresh tokens
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


class AuthService:
    """Authentication service for JWT token management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.jwt_secret_key, 
            algorithm=settings.jwt_algorithm
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=30)  # Refresh tokens last 30 days
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        # Store refresh token in Redis with expiration
        redis_client.setex(
            f"refresh_token:{user_id}",
            timedelta(days=30),
            encoded_jwt
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            # Check if token is blacklisted
            if redis_client.get(f"blacklist:{token}"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @staticmethod
    def blacklist_token(token: str, expires_at: datetime):
        """Add token to blacklist in Redis"""
        ttl = int((expires_at - datetime.utcnow()).total_seconds())
        if ttl > 0:
            redis_client.setex(f"blacklist:{token}", ttl, "true")
    
    @staticmethod
    def revoke_refresh_token(user_id: str):
        """Revoke a user's refresh token"""
        redis_client.delete(f"refresh_token:{user_id}")
    
    @staticmethod
    def get_refresh_token(user_id: str) -> Optional[str]:
        """Get stored refresh token for user"""
        return redis_client.get(f"refresh_token:{user_id}")
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Get current user from JWT token"""
        payload = AuthService.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        return user
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """Create new access token from refresh token"""
        payload = AuthService.verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify refresh token exists in Redis
        stored_token = AuthService.get_refresh_token(user_id)
        if not stored_token or stored_token != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or invalid"
            )
        
        # Create new access token
        new_token = AuthService.create_access_token(data={"sub": user_id})
        
        return new_token


# Utility functions for FastAPI dependencies
def get_password_hash(password: str) -> str:
    """Utility function to hash password"""
    return AuthService.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Utility function to verify password"""
    return AuthService.verify_password(plain_password, hashed_password)