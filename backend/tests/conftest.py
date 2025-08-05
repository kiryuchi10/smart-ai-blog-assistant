"""
Test configuration and fixtures
"""

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User, SubscriptionPlan


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def sample_subscription_plan(db_session):
    """Create a sample subscription plan for testing"""
    plan = SubscriptionPlan(
        name="Test Plan",
        description="Test subscription plan",
        price_monthly=29.99,
        price_yearly=299.99,
        posts_limit=100,
        api_calls_limit=1000,
        storage_limit_gb=10,
        folder_monitoring=True,
        comment_analysis=True,
        advanced_analytics=False,
        priority_support=True,
        multi_platform_publishing=True,
        ai_content_enhancement=True,
        api_data_integration=True,
        custom_templates=True,
        bulk_operations=False,
        white_label=False,
        trial_days=14,
        is_active=True,
        sort_order=1,
    )
    
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    
    return plan


@pytest_asyncio.fixture
async def sample_user(db_session, sample_subscription_plan):
    """Create a sample user for testing"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        subscription_tier="starter",
        subscription_plan_id=sample_subscription_plan.id,
        posts_limit=100,
        api_calls_limit=1000,
        folder_monitoring_enabled=True,
        comment_analysis_enabled=True,
        preferred_platforms=["wordpress", "medium"],
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user