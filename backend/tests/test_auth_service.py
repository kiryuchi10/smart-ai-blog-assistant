"""
Unit tests for authentication service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.auth_service import AuthService
from app.models.user import User
import uuid

# Mock Redis client for all tests
@pytest.fixture(autouse=True)
def mock_redis():
    with patch('app.services.auth_service.redis_client') as mock:
        mock.get.return_value = None  # Default: no blacklisted tokens
        mock.setex.return_value = True
        mock.delete.return_value = True
        yield mock


class TestAuthService:
    """Test cases for AuthService"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60 characters
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_verify_password_success(self):
        """Test successful password verification"""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(password, hashed) is True
    
    def test_verify_password_failure(self):
        """Test failed password verification"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(wrong_password, hashed) is False
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = AuthService.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        
        # Verify token can be decoded
        payload = AuthService.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
    
    def test_create_access_token_with_expiration(self):
        """Test access token creation with custom expiration"""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=30)
        
        token = AuthService.create_access_token(data, expires_delta)
        payload = AuthService.verify_token(token)
        
        # Check that expiration is approximately 30 minutes from now
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        
        # Allow 2 minute tolerance for test execution time
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 120  # 2 minutes tolerance
    
    def test_create_refresh_token(self, mock_redis):
        """Test refresh token creation"""
        user_id = str(uuid.uuid4())
        token = AuthService.create_refresh_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Verify token can be decoded
        payload = AuthService.verify_token(token, "refresh")
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        
        # Verify Redis was called to store token
        mock_redis.setex.assert_called_once()
    
    def test_verify_token_success(self):
        """Test successful token verification"""
        data = {"sub": "user123"}
        token = AuthService.create_access_token(data)
        
        payload = AuthService.verify_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
    
    def test_verify_token_blacklisted(self, mock_redis):
        """Test token verification with blacklisted token"""
        mock_redis.get.return_value = "true"  # Token is blacklisted
        
        data = {"sub": "user123"}
        token = AuthService.create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "validate credentials" in exc_info.value.detail
    
    def test_verify_token_wrong_type(self):
        """Test token verification with wrong token type"""
        data = {"sub": "user123"}
        access_token = AuthService.create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token(access_token, "refresh")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail
    
    def test_blacklist_token(self, mock_redis):
        """Test token blacklisting"""
        token = "test.token.here"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        AuthService.blacklist_token(token, expires_at)
        
        mock_redis.setex.assert_called()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"blacklist:{token}"
        assert call_args[0][2] == "true"
    
    def test_revoke_refresh_token(self, mock_redis):
        """Test refresh token revocation"""
        user_id = "user123"
        
        AuthService.revoke_refresh_token(user_id)
        
        mock_redis.delete.assert_called_with(f"refresh_token:{user_id}")
    
    def test_get_refresh_token(self, mock_redis):
        """Test getting stored refresh token"""
        user_id = "user123"
        expected_token = "stored.refresh.token"
        mock_redis.get.return_value = expected_token
        
        result = AuthService.get_refresh_token(user_id)
        
        assert result == expected_token
        mock_redis.get.assert_called_with(f"refresh_token:{user_id}")
    
    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Create mock user
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.password_hash = AuthService.hash_password("password123")
        mock_user.is_active = True
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = AuthService.authenticate_user(mock_db, "test@example.com", "password123")
        
        assert result == mock_user
    
    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user"""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = AuthService.authenticate_user(mock_db, "nonexistent@example.com", "password")
        
        assert result is None
    
    def test_authenticate_user_inactive(self):
        """Test authentication with inactive user"""
        mock_db = Mock(spec=Session)
        
        mock_user = Mock(spec=User)
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.authenticate_user(mock_db, "test@example.com", "password")
        
        assert exc_info.value.status_code == 401
        assert "deactivated" in exc_info.value.detail
    
    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password"""
        mock_db = Mock(spec=Session)
        
        mock_user = Mock(spec=User)
        mock_user.password_hash = AuthService.hash_password("correct_password")
        mock_user.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = AuthService.authenticate_user(mock_db, "test@example.com", "wrong_password")
        
        assert result is None
    
    def test_get_current_user_success(self):
        """Test getting current user from valid token"""
        mock_db = Mock(spec=Session)
        
        # Create mock user
        user_id = str(uuid.uuid4())
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Create valid token
        token = AuthService.create_access_token({"sub": user_id})
        
        result = AuthService.get_current_user(mock_db, token)
        
        assert result == mock_user
    
    def test_get_current_user_not_found(self):
        """Test getting current user when user doesn't exist"""
        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user_id = str(uuid.uuid4())
        token = AuthService.create_access_token({"sub": user_id})
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.get_current_user(mock_db, token)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail
    
    def test_get_current_user_inactive(self):
        """Test getting current user when user is inactive"""
        mock_db = Mock(spec=Session)
        
        user_id = str(uuid.uuid4())
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = False
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        token = AuthService.create_access_token({"sub": user_id})
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.get_current_user(mock_db, token)
        
        assert exc_info.value.status_code == 401
        assert "deactivated" in exc_info.value.detail
    
    def test_refresh_access_token_success(self, mock_redis):
        """Test successful access token refresh"""
        user_id = str(uuid.uuid4())
        refresh_token = AuthService.create_refresh_token(user_id)
        
        # Mock Redis to return the stored token when checking for refresh token
        def mock_get(key):
            if key.startswith("refresh_token:"):
                return refresh_token
            return None  # No blacklisted tokens
        
        mock_redis.get.side_effect = mock_get
        
        new_token = AuthService.refresh_access_token(refresh_token)
        
        assert isinstance(new_token, str)
        assert len(new_token) > 100
        
        # Verify new token is valid
        payload = AuthService.verify_token(new_token)
        assert payload["sub"] == user_id
    
    def test_refresh_access_token_not_stored(self, mock_redis):
        """Test access token refresh with token not in Redis"""
        user_id = str(uuid.uuid4())
        refresh_token = AuthService.create_refresh_token(user_id)
        
        # Mock Redis to return None (token not found)
        mock_redis.get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.refresh_access_token(refresh_token)
        
        assert exc_info.value.status_code == 401
        assert "not found" in exc_info.value.detail