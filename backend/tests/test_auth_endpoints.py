"""
Integration tests for authentication API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.services.auth_service import AuthService
import json

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Disable startup event for testing
app.router.on_startup = []

# Create test client with custom base URL to match allowed hosts
client = TestClient(app, base_url="http://localhost")


@pytest.fixture(autouse=True)
def setup_database():
    """Setup and teardown test database"""
    # Drop tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_redis():
    """Mock Redis client for all tests"""
    with patch('app.services.auth_service.redis_client') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.delete.return_value = True
        mock.incr.return_value = 1
        mock.ttl.return_value = 60
        yield mock


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for all tests"""
    with patch('app.services.rate_limiter.redis_client') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.incr.return_value = 1
        mock.ttl.return_value = 60
        yield mock


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user_success(self, mock_redis, mock_rate_limiter):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_register_user_duplicate_email(self, mock_redis, mock_rate_limiter):
        """Test registration with duplicate email"""
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        
        # First registration should succeed
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Second registration should fail
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_register_user_invalid_password(self, mock_redis, mock_rate_limiter):
        """Test registration with invalid password"""
        user_data = {
            "email": "test@example.com",
            "password": "weak"  # Too short, no uppercase, no digit
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_user_invalid_email(self, mock_redis, mock_rate_limiter):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "TestPass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_login_user_success(self, mock_redis, mock_rate_limiter):
        """Test successful user login"""
        # First register a user
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_user_invalid_credentials(self, mock_redis, mock_rate_limiter):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_user_wrong_password(self, mock_redis, mock_rate_limiter):
        """Test login with wrong password"""
        # Register user
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Login with wrong password
        login_data = {
            "email": "test@example.com",
            "password": "WrongPass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_refresh_token_success(self, mock_redis, mock_rate_limiter):
        """Test successful token refresh"""
        # Register and get tokens
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        tokens = register_response.json()
        
        # Mock Redis to return the refresh token
        def mock_get(key):
            if key.startswith("refresh_token:"):
                return tokens["refresh_token"]
            return None
        
        mock_redis.get.side_effect = mock_get
        
        # Refresh token
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == tokens["refresh_token"]
    
    def test_refresh_token_invalid(self, mock_redis, mock_rate_limiter):
        """Test refresh with invalid token"""
        refresh_data = {
            "refresh_token": "invalid.refresh.token"
        }
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
    
    def test_get_current_user_success(self, mock_redis, mock_rate_limiter):
        """Test getting current user info"""
        # Register and get token
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123",
            "first_name": "Test",
            "last_name": "User"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        tokens = register_response.json()
        
        # Get user info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["subscription_tier"] == "free"
    
    def test_get_current_user_unauthorized(self, mock_redis, mock_rate_limiter):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # No authorization header
    
    def test_get_current_user_invalid_token(self, mock_redis, mock_rate_limiter):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_logout_success(self, mock_redis, mock_rate_limiter):
        """Test successful logout"""
        # Register and get token
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        tokens = register_response.json()
        
        # Logout
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"]
    
    def test_logout_unauthorized(self, mock_redis, mock_rate_limiter):
        """Test logout without token"""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 403
    
    def test_password_reset_request(self, mock_redis, mock_rate_limiter):
        """Test password reset request"""
        # Register user first
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Request password reset
        reset_data = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        
        assert response.status_code == 200
        assert "reset link" in response.json()["message"]
    
    def test_password_reset_nonexistent_email(self, mock_redis, mock_rate_limiter):
        """Test password reset for nonexistent email"""
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "reset link" in response.json()["message"]
    
    def test_password_reset_confirm_success(self, mock_redis, mock_rate_limiter):
        """Test password reset confirmation"""
        # Register user
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Mock Redis to return user ID for reset token
        mock_redis.get.return_value = "some-user-id"
        
        # Confirm password reset
        reset_data = {
            "token": "valid-reset-token",
            "new_password": "NewPass456"
        }
        
        response = client.post("/api/v1/auth/password-reset/confirm", json=reset_data)
        
        assert response.status_code == 200
        assert "successfully reset" in response.json()["message"]
    
    def test_password_reset_confirm_invalid_token(self, mock_redis, mock_rate_limiter):
        """Test password reset confirmation with invalid token"""
        # Mock Redis to return None (token not found)
        mock_redis.get.return_value = None
        
        reset_data = {
            "token": "invalid-token",
            "new_password": "NewPass456"
        }
        
        response = client.post("/api/v1/auth/password-reset/confirm", json=reset_data)
        
        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]
    
    def test_rate_limiting(self, mock_rate_limiter):
        """Test rate limiting on auth endpoints"""
        # Mock rate limiter to simulate rate limit exceeded
        mock_rate_limiter.get.return_value = "5"  # Already at limit
        
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]