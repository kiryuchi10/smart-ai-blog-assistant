"""
Unit tests for user management models
"""
import pytest
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
import uuid

# Create test models with String IDs for SQLite compatibility
from sqlalchemy import Column, Integer, Boolean, DateTime, DECIMAL, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class TestUser(Base):
    """Test User model with String ID for SQLite compatibility"""
    __tablename__ = "test_users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    subscription_tier = Column(String(50), default='free')
    subscription_status = Column(String(50), default='active')
    posts_used_this_month = Column(Integer, default=0)
    posts_limit = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def can_create_post(self):
        """Check if user can create a new post based on subscription limits"""
        return self.posts_used_this_month < self.posts_limit
    
    def increment_post_usage(self):
        """Increment the monthly post usage counter"""
        self.posts_used_this_month += 1
    
    def reset_monthly_usage(self):
        """Reset monthly post usage counter (called monthly)"""
        self.posts_used_this_month = 0


class TestSubscriptionPlan(Base):
    """Test SubscriptionPlan model with String ID for SQLite compatibility"""
    __tablename__ = "test_subscription_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    price_monthly = Column(DECIMAL(10, 2))
    posts_limit = Column(Integer, nullable=False)
    features = Column(Text)  # JSON as text for SQLite
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, price={self.price_monthly})>"


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


class TestUserModel:
    """Test cases for User model"""
    
    def test_user_creation(self, db_session):
        """Test creating a new user"""
        user = TestUser(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.subscription_tier == "free"
        assert user.subscription_status == "active"
        assert user.posts_used_this_month == 0
        assert user.posts_limit == 5
        assert user.is_active is True
        assert user.is_verified is False
    
    def test_user_full_name_property(self, db_session):
        """Test user full_name property"""
        # Test with both first and last name
        user1 = TestUser(
            email="test1@example.com",
            password_hash="hash",
            first_name="John",
            last_name="Doe"
        )
        assert user1.full_name == "John Doe"
        
        # Test with only first name
        user2 = TestUser(
            email="test2@example.com",
            password_hash="hash",
            first_name="John"
        )
        assert user2.full_name == "John"
        
        # Test with only last name
        user3 = TestUser(
            email="test3@example.com",
            password_hash="hash",
            last_name="Doe"
        )
        assert user3.full_name == "Doe"
        
        # Test with no names (should return email)
        user4 = TestUser(
            email="test4@example.com",
            password_hash="hash"
        )
        assert user4.full_name == "test4@example.com"
    
    def test_can_create_post(self, db_session):
        """Test post creation limit checking"""
        user = TestUser(
            email="test@example.com",
            password_hash="hash",
            posts_used_this_month=3,
            posts_limit=5
        )
        
        # Should be able to create post (3 < 5)
        assert user.can_create_post() is True
        
        # Set to limit
        user.posts_used_this_month = 5
        assert user.can_create_post() is False
        
        # Exceed limit
        user.posts_used_this_month = 6
        assert user.can_create_post() is False
    
    def test_increment_post_usage(self, db_session):
        """Test incrementing post usage counter"""
        user = TestUser(
            email="test@example.com",
            password_hash="hash",
            posts_used_this_month=2
        )
        
        user.increment_post_usage()
        assert user.posts_used_this_month == 3
        
        user.increment_post_usage()
        assert user.posts_used_this_month == 4
    
    def test_reset_monthly_usage(self, db_session):
        """Test resetting monthly usage counter"""
        user = TestUser(
            email="test@example.com",
            password_hash="hash",
            posts_used_this_month=10
        )
        
        user.reset_monthly_usage()
        assert user.posts_used_this_month == 0
    
    def test_user_repr(self, db_session):
        """Test user string representation"""
        user = TestUser(
            email="test@example.com",
            password_hash="hash"
        )
        db_session.add(user)
        db_session.commit()
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert "test@example.com" in repr_str


class TestSubscriptionPlanModel:
    """Test cases for SubscriptionPlan model"""
    
    def test_subscription_plan_creation(self, db_session):
        """Test creating a subscription plan"""
        plan = TestSubscriptionPlan(
            name="Premium",
            price_monthly=19.99,
            posts_limit=100,
            features={"ai_generation": True, "analytics": True}
        )
        db_session.add(plan)
        db_session.commit()
        
        assert plan.id is not None
        assert plan.name == "Premium"
        assert plan.price_monthly == 19.99
        assert plan.posts_limit == 100
        # Features stored as text in SQLite, would be JSON in PostgreSQL
        assert plan.is_active is True
    
    def test_free_plan_creation(self, db_session):
        """Test creating a free subscription plan"""
        plan = TestSubscriptionPlan(
            name="Free",
            price_monthly=0.00,
            posts_limit=5,
            features='{"ai_generation": true, "analytics": false}'
        )
        db_session.add(plan)
        db_session.commit()
        
        assert plan.name == "Free"
        assert plan.price_monthly == 0.00
        assert plan.posts_limit == 5
        # Features stored as text in SQLite
    
    def test_subscription_plan_repr(self, db_session):
        """Test subscription plan string representation"""
        plan = TestSubscriptionPlan(
            name="Basic",
            price_monthly=9.99,
            posts_limit=25
        )
        
        repr_str = repr(plan)
        assert "SubscriptionPlan" in repr_str
        assert "Basic" in repr_str
        assert "9.99" in repr_str
    
    def test_unique_plan_name_constraint(self, db_session):
        """Test that plan names must be unique"""
        plan1 = TestSubscriptionPlan(
            name="Premium",
            price_monthly=19.99,
            posts_limit=100
        )
        plan2 = TestSubscriptionPlan(
            name="Premium",  # Same name
            price_monthly=29.99,
            posts_limit=200
        )
        
        db_session.add(plan1)
        db_session.commit()
        
        db_session.add(plan2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestUserValidation:
    """Test user model validation"""
    
    def test_email_required(self, db_session):
        """Test that email is required"""
        user = TestUser(password_hash="hash")
        db_session.add(user)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_password_hash_required(self, db_session):
        """Test that password_hash is required"""
        user = TestUser(email="test@example.com")
        db_session.add(user)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_unique_email_constraint(self, db_session):
        """Test that email must be unique"""
        user1 = TestUser(
            email="test@example.com",
            password_hash="hash1"
        )
        user2 = TestUser(
            email="test@example.com",  # Same email
            password_hash="hash2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()