"""
Unit tests for analytics models
"""
import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.analytics import (
    PostAnalytics, CommentAnalysis, ContentRecommendation, 
    PerformanceSummary, APIDataRequest
)
from app.models.user import User
from app.models.content import BlogPost


class TestPostAnalytics:
    """Test PostAnalytics model"""
    
    def test_create_post_analytics(self, db_session: Session, sample_blog_post: BlogPost):
        """Test creating post analytics"""
        analytics = PostAnalytics(
            post_id=sample_blog_post.id,
            platform="wordpress",
            views=1000,
            unique_views=800,
            likes=50,
            shares=25,
            comments=10,
            time_on_page=180,
            search_impressions=500,
            search_clicks=100
        )
        
        db_session.add(analytics)
        db_session.commit()
        
        assert analytics.id is not None
        assert analytics.platform == "wordpress"
        assert analytics.views == 1000
        assert analytics.unique_views == 800
        assert analytics.engagement_rate == 0  # Default value
    
    def test_calculate_engagement_rate(self, db_session: Session, sample_blog_post: BlogPost):
        """Test engagement rate calculation"""
        analytics = PostAnalytics(
            post_id=sample_blog_post.id,
            platform="medium",
            views=1000,
            likes=50,
            shares=25,
            comments=10
        )
        
        db_session.add(analytics)
        db_session.commit()
        
        # Calculate engagement rate
        engagement_rate = analytics.calculate_engagement_rate()
        expected_rate = (50 + 25 + 10) / 1000  # 0.085
        
        assert engagement_rate == expected_rate
        assert analytics.engagement_rate == expected_rate
    
    def test_zero_views_engagement_rate(self, db_session: Session, sample_blog_post: BlogPost):
        """Test engagement rate calculation with zero views"""
        analytics = PostAnalytics(
            post_id=sample_blog_post.id,
            platform="ghost",
            views=0,
            likes=5,
            shares=2,
            comments=1
        )
        
        db_session.add(analytics)
        db_session.commit()
        
        engagement_rate = analytics.calculate_engagement_rate()
        assert engagement_rate == 0
        assert analytics.engagement_rate == 0


class TestCommentAnalysis:
    """Test CommentAnalysis model"""
    
    def test_create_comment_analysis(self, db_session: Session, sample_blog_post: BlogPost):
        """Test creating comment analysis"""
        analysis = CommentAnalysis(
            post_id=sample_blog_post.id,
            platform="wordpress",
            comment_text="This is a great article! Very helpful.",
            comment_author="john_doe",
            comment_id="wp_comment_123",
            sentiment_score=Decimal("0.85"),
            sentiment_label="positive",
            extracted_questions=["How do I implement this?"],
            extracted_complaints=[],
            extracted_suggestions=["Add more examples"],
            emotion_detected="joy",
            topics_mentioned=["implementation", "examples"],
            confidence_score=Decimal("0.92")
        )
        
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.id is not None
        assert analysis.platform == "wordpress"
        assert analysis.sentiment_label == "positive"
        assert analysis.sentiment_score == Decimal("0.85")
        assert analysis.extracted_questions == ["How do I implement this?"]
        assert analysis.is_spam is False
    
    def test_negative_sentiment_analysis(self, db_session: Session, sample_blog_post: BlogPost):
        """Test negative sentiment comment analysis"""
        analysis = CommentAnalysis(
            post_id=sample_blog_post.id,
            platform="medium",
            comment_text="This article is confusing and poorly written.",
            comment_author="critic_user",
            sentiment_score=Decimal("-0.65"),
            sentiment_label="negative",
            extracted_complaints=["confusing content", "poor writing"],
            emotion_detected="frustration"
        )
        
        db_session.add(analysis)
        db_session.commit()
        
        assert analysis.sentiment_label == "negative"
        assert analysis.sentiment_score == Decimal("-0.65")
        assert "confusing content" in analysis.extracted_complaints


class TestContentRecommendation:
    """Test ContentRecommendation model"""
    
    def test_create_content_recommendation(self, db_session: Session, sample_user: User, sample_blog_post: BlogPost):
        """Test creating content recommendation"""
        recommendation = ContentRecommendation(
            user_id=sample_user.id,
            post_id=sample_blog_post.id,
            recommendation_type="seo_improvement",
            recommendation_text="Add more relevant keywords to improve SEO ranking",
            priority_score=8,
            status="pending",
            expected_impact="high",
            implementation_difficulty="easy",
            category="seo",
            source_data={"keywords_missing": ["python", "tutorial"]}
        )
        
        db_session.add(recommendation)
        db_session.commit()
        
        assert recommendation.id is not None
        assert recommendation.recommendation_type == "seo_improvement"
        assert recommendation.priority_score == 8
        assert recommendation.status == "pending"
        assert recommendation.expected_impact == "high"
    
    def test_follow_up_topic_recommendation(self, db_session: Session, sample_user: User):
        """Test follow-up topic recommendation without specific post"""
        recommendation = ContentRecommendation(
            user_id=sample_user.id,
            post_id=None,  # General recommendation
            recommendation_type="follow_up_topic",
            recommendation_text="Write about advanced Python decorators based on reader questions",
            priority_score=6,
            category="content_strategy",
            source_data={"reader_questions": ["How to create custom decorators?"]}
        )
        
        db_session.add(recommendation)
        db_session.commit()
        
        assert recommendation.post_id is None
        assert recommendation.recommendation_type == "follow_up_topic"
        assert recommendation.category == "content_strategy"


class TestPerformanceSummary:
    """Test PerformanceSummary model"""
    
    def test_create_performance_summary(self, db_session: Session, sample_blog_post: BlogPost):
        """Test creating performance summary"""
        summary = PerformanceSummary(
            post_id=sample_blog_post.id,
            total_views=5000,
            total_engagement=250,
            best_performing_platform="wordpress",
            overall_sentiment_score=Decimal("0.75"),
            seo_performance_score=85,
            recommendation_count=3,
            total_likes=150,
            total_shares=75,
            total_comments=25,
            average_engagement_rate=Decimal("0.05"),
            views_trend="increasing",
            engagement_trend="stable",
            sentiment_trend="positive",
            readability_score=78,
            seo_optimization_score=82,
            content_uniqueness_score=90
        )
        
        db_session.add(summary)
        db_session.commit()
        
        assert summary.id is not None
        assert summary.total_views == 5000
        assert summary.best_performing_platform == "wordpress"
        assert summary.views_trend == "increasing"
    
    def test_calculate_overall_score(self, db_session: Session, sample_blog_post: BlogPost):
        """Test overall score calculation"""
        summary = PerformanceSummary(
            post_id=sample_blog_post.id,
            seo_performance_score=80,
            readability_score=75,
            seo_optimization_score=85,
            content_uniqueness_score=90
        )
        
        db_session.add(summary)
        db_session.commit()
        
        overall_score = summary.calculate_overall_score()
        expected_score = (80 + 75 + 85 + 90) / 4  # 82.5
        
        assert overall_score == expected_score


class TestAPIDataRequest:
    """Test APIDataRequest model"""
    
    def test_create_api_data_request(self, db_session: Session, sample_user: User, sample_blog_post: BlogPost):
        """Test creating API data request"""
        request = APIDataRequest(
            user_id=sample_user.id,
            post_id=sample_blog_post.id,
            api_source="yahoo_finance",
            request_parameters={"symbol": "AAPL", "period": "1mo"},
            response_data={"prices": [150.0, 152.0, 148.0]},
            charts_generated=["price_chart.png", "volume_chart.png"],
            status="completed",
            request_type="stock_data",
            data_points_retrieved=30,
            processing_time_ms=1500,
            cost_credits=Decimal("0.05")
        )
        
        db_session.add(request)
        db_session.commit()
        
        assert request.id is not None
        assert request.api_source == "yahoo_finance"
        assert request.status == "completed"
        assert request.data_points_retrieved == 30
        assert request.cost_credits == Decimal("0.05")
        assert "price_chart.png" in request.charts_generated
    
    def test_failed_api_request(self, db_session: Session, sample_user: User):
        """Test failed API data request"""
        request = APIDataRequest(
            user_id=sample_user.id,
            api_source="alpha_vantage",
            request_parameters={"symbol": "INVALID"},
            status="failed",
            error_message="Invalid symbol provided",
            retry_count=2
        )
        
        db_session.add(request)
        db_session.commit()
        
        assert request.status == "failed"
        assert request.error_message == "Invalid symbol provided"
        assert request.retry_count == 2
        assert request.data_points_retrieved == 0