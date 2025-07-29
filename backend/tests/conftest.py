"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.core.auth_middleware import get_current_user
from app.models.user import User


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    user = MagicMock(spec=User)
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.subscription_tier = "basic"
    user.posts_used_this_month = 5
    user.posts_limit = 50
    user.is_active = True
    user.is_verified = True
    return user


@pytest.fixture
def authenticated_client(mock_user):
    """Create a test client with mocked authentication"""
    def mock_get_current_user():
        return mock_user
    
    # Override the dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    client = TestClient(app)
    
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create a test client without authentication"""
    return TestClient(app)