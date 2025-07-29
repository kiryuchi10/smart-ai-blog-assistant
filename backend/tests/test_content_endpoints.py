"""
Integration tests for content generation API endpoints
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.openai_service import GeneratedContent, TokenUsage


@pytest.fixture
def mock_generated_content():
    """Mock generated content response"""
    return GeneratedContent(
        title="How to Improve Your Website SEO: A Complete Guide",
        content="# How to Improve Your Website SEO\n\nSEO is crucial for online success...",
        meta_description="Learn how to improve your website SEO with proven strategies.",
        keywords=["SEO", "website optimization", "search rankings"],
        seo_suggestions=[
            "Include target keywords in title and headings",
            "Optimize meta descriptions for click-through rates"
        ],
        token_usage=TokenUsage(
            prompt_tokens=150,
            completion_tokens=800,
            total_tokens=950,
            estimated_cost=0.025
        )
    )


class TestContentGenerationEndpoints:
    """Test cases for content generation endpoints"""
    
    @patch('app.api.v1.endpoints.content.get_openai_service')
    @patch('app.api.v1.endpoints.content.rate_limiter.check_rate_limit')
    @patch('app.api.v1.endpoints.content.check_usage_limits')
    def test_generate_content_success(
        self,
        mock_check_limits,
        mock_rate_limit,
        mock_get_service,
        authenticated_client,
        mock_user,
        mock_generated_content
    ):
        """Test successful content generation"""
        # Setup mocks
        mock_rate_limit.return_value = None
        mock_check_limits.return_value = None
        
        mock_service = AsyncMock()
        mock_service.generate_content.return_value = mock_generated_content
        mock_get_service.return_value = mock_service
        
        # Test request
        request_data = {
            "topic": "How to improve website SEO",
            "content_type": "how_to",
            "tone": "professional",
            "keywords": ["SEO", "website optimization"],
            "target_length": 1000,
            "include_seo": True,
            "industry": "Digital Marketing"
        }
        
        response = authenticated_client.post("/api/v1/content/generate", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == mock_generated_content.title
        assert data["content"] == mock_generated_content.content
        assert data["meta_description"] == mock_generated_content.meta_description
        assert data["keywords"] == mock_generated_content.keywords
        assert data["seo_suggestions"] == mock_generated_content.seo_suggestions
        assert data["word_count"] > 0
        assert data["reading_time"] > 0
        assert "token_usage" in data
        
        # Verify service was called correctly
        mock_service.generate_content.assert_called_once()
        call_args = mock_service.generate_content.call_args[0][0]
        assert call_args.topic == request_data["topic"]
        assert call_args.target_length == request_data["target_length"]
    
    @patch('app.api.v1.endpoints.content.rate_limiter.check_rate_limit')
    def test_generate_content_rate_limit_exceeded(
        self,
        mock_rate_limit,
        authenticated_client,
        mock_user
    ):
        """Test content generation with rate limit exceeded"""
        from fastapi import HTTPException
        
        mock_rate_limit.side_effect = HTTPException(status_code=429, detail="Rate limit exceeded")
        
        request_data = {
            "topic": "Test topic",
            "content_type": "article"
        }
        
        response = authenticated_client.post("/api/v1/content/generate", json=request_data)
        
        assert response.status_code == 429
    
    @patch('app.api.v1.endpoints.content.get_openai_service')
    @patch('app.api.v1.endpoints.content.rate_limiter.check_rate_limit')
    @patch('app.api.v1.endpoints.content.check_usage_limits')
    def test_generate_content_openai_error(
        self,
        mock_check_limits,
        mock_rate_limit,
        mock_get_service,
        authenticated_client,
        mock_user
    ):
        """Test content generation with OpenAI service error"""
        from app.services.openai_service import OpenAIServiceError
        
        mock_rate_limit.return_value = None
        mock_check_limits.return_value = None
        
        mock_service = AsyncMock()
        mock_service.generate_content.side_effect = OpenAIServiceError("API error")
        mock_get_service.return_value = mock_service
        
        request_data = {
            "topic": "Test topic",
            "content_type": "article"
        }
        
        response = authenticated_client.post("/api/v1/content/generate", json=request_data)
        
        assert response.status_code == 503
        assert "Content generation service unavailable" in response.json()["detail"]
    
    def test_generate_content_invalid_request(self, authenticated_client):
        """Test content generation with invalid request data"""
        request_data = {
            "topic": "",  # Empty topic
            "content_type": "invalid_type",
            "target_length": 50  # Too short
        }
        
        response = authenticated_client.post("/api/v1/content/generate", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.v1.endpoints.content.get_openai_service')
    @patch('app.api.v1.endpoints.content.rate_limiter.check_rate_limit')
    def test_regenerate_content_section_success(
        self,
        mock_rate_limit,
        mock_get_service,
        authenticated_client,
        mock_user
    ):
        """Test successful content section regeneration"""
        mock_rate_limit.return_value = None
        
        mock_service = AsyncMock()
        mock_service.regenerate_section.return_value = "Regenerated section content"
        mock_get_service.return_value = mock_service
        
        request_data = {
            "original_content": "This is the original blog post content with multiple sections. It contains detailed information about various topics and provides comprehensive coverage of the subject matter. The content is well-structured and informative.",
            "section_to_regenerate": "This specific section needs improvement and should be more engaging",
            "instructions": "Make it more engaging and add examples"
        }
        
        response = authenticated_client.post("/api/v1/content/regenerate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["regenerated_section"] == "Regenerated section content"
        assert "token_usage" in data
        
        mock_service.regenerate_section.assert_called_once_with(
            request_data["original_content"],
            request_data["section_to_regenerate"],
            request_data["instructions"]
        )
    
    @patch('app.api.v1.endpoints.content.get_openai_service')
    @patch('app.api.v1.endpoints.content.rate_limiter.check_rate_limit')
    def test_analyze_seo_success(
        self,
        mock_rate_limit,
        mock_get_service,
        authenticated_client,
        mock_user
    ):
        """Test successful SEO analysis"""
        mock_rate_limit.return_value = None
        
        mock_service = AsyncMock()
        mock_service.get_seo_suggestions.return_value = [
            "Add more internal links",
            "Optimize image alt tags",
            "Improve page loading speed"
        ]
        mock_get_service.return_value = mock_service
        
        request_data = {
            "content": "This is a sample blog post about SEO optimization techniques. SEO is very important for website visibility. Optimization helps improve search rankings. These techniques are essential for digital marketing success.",
            "target_keywords": ["SEO", "optimization", "techniques"]
        }
        
        response = authenticated_client.post("/api/v1/content/analyze-seo", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "seo_score" in data
        assert 0 <= data["seo_score"] <= 100
        assert "suggestions" in data
        assert len(data["suggestions"]) == 3
        assert "keyword_density" in data
        assert "readability_score" in data
        assert "token_usage" in data
        
        # Check keyword density structure
        for keyword in request_data["target_keywords"]:
            assert keyword in data["keyword_density"]
            assert "count" in data["keyword_density"][keyword]
            assert "density" in data["keyword_density"][keyword]
    
    def test_validate_content_success(
        self,
        authenticated_client,
        mock_user
    ):
        """Test successful content validation"""
        request_data = {
            "content": "This is a valid blog post content with sufficient length and proper structure."
        }
        
        response = authenticated_client.post("/api/v1/content/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data
    
    def test_validate_content_with_errors(
        self,
        authenticated_client,
        mock_user
    ):
        """Test content validation with errors"""
        # Content with harmful script
        request_data = {
            "content": "Short content <script>alert('xss')</script>"
        }
        
        response = authenticated_client.post("/api/v1/content/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] == False
        assert len(data["errors"]) > 0
        assert "sanitized_content" in data
    
    def test_content_generation_request_validation(self, authenticated_client):
        """Test content generation request validation"""
        # Test with invalid keywords (too many)
        request_data = {
            "topic": "Valid topic",
            "keywords": ["keyword" + str(i) for i in range(15)]  # Too many keywords
        }
        
        response = authenticated_client.post("/api/v1/content/generate", json=request_data)
        assert response.status_code == 422
        
        # Test with invalid target length
        request_data = {
            "topic": "Valid topic",
            "target_length": 100  # Too short
        }
        
        response = authenticated_client.post("/api/v1/content/generate", json=request_data)
        assert response.status_code == 422
    
    def test_seo_analysis_request_validation(self, authenticated_client):
        """Test SEO analysis request validation"""
        # Test with empty keywords
        request_data = {
            "content": "Valid content for analysis",
            "target_keywords": []  # Empty keywords
        }
        
        response = authenticated_client.post("/api/v1/content/analyze-seo", json=request_data)
        assert response.status_code == 422
        
        # Test with too short keywords
        request_data = {
            "content": "Valid content for analysis",
            "target_keywords": ["a"]  # Too short keyword
        }
        
        response = authenticated_client.post("/api/v1/content/analyze-seo", json=request_data)
        assert response.status_code == 422
    
    @patch('app.api.v1.endpoints.content.get_openai_service')
    @patch('app.api.v1.endpoints.content.rate_limiter.check_rate_limit')
    @patch('app.api.v1.endpoints.content.check_usage_limits')
    def test_generate_content_stream_success(
        self,
        mock_check_limits,
        mock_rate_limit,
        mock_get_service,
        authenticated_client,
        mock_user
    ):
        """Test successful streaming content generation"""
        mock_rate_limit.return_value = None
        mock_check_limits.return_value = None
        
        async def mock_stream():
            yield "This is "
            yield "streaming "
            yield "content."
        
        mock_service = AsyncMock()
        mock_service.generate_content_stream.return_value = mock_stream()
        mock_get_service.return_value = mock_service
        
        request_data = {
            "topic": "How to improve website SEO",
            "content_type": "how_to",
            "tone": "professional"
        }
        
        response = authenticated_client.post("/api/v1/content/generate/stream", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"


class TestContentUtilityFunctions:
    """Test utility functions used in content endpoints"""
    
    def test_calculate_reading_time(self):
        """Test reading time calculation"""
        from app.api.v1.endpoints.content import _calculate_reading_time
        
        # Test with short content
        short_content = "This is a short piece of content."
        assert _calculate_reading_time(short_content) == 1
        
        # Test with longer content (approximately 450 words = 2 minutes)
        long_content = " ".join(["word"] * 450)
        assert _calculate_reading_time(long_content) == 2
    
    def test_count_words(self):
        """Test word counting"""
        from app.api.v1.endpoints.content import _count_words
        
        content = "This is a test content with <b>HTML</b> tags."
        word_count = _count_words(content)
        assert word_count == 8  # HTML tags should be removed
    
    def test_calculate_seo_score(self):
        """Test SEO score calculation"""
        from app.api.v1.endpoints.content import _calculate_seo_score
        
        content = """# SEO Optimization Guide
        
        This is a comprehensive guide about SEO optimization techniques.
        SEO is important for website visibility. Learn about optimization strategies.
        """
        
        keywords = ["SEO", "optimization"]
        score = _calculate_seo_score(content, keywords)
        
        assert 0 <= score <= 100
        assert isinstance(score, int)
    
    def test_calculate_readability_score(self):
        """Test readability score calculation"""
        from app.api.v1.endpoints.content import _calculate_readability_score
        
        content = "This is a simple sentence. It has good readability."
        score = _calculate_readability_score(content)
        
        assert 0.0 <= score <= 100.0
        assert isinstance(score, float)
    
    def test_content_validation(self):
        """Test content validation function"""
        from app.api.v1.endpoints.content import _validate_content
        
        # Test valid content (needs to be at least 100 characters)
        valid_content = "This is a valid blog post with sufficient length and proper structure for testing purposes. It contains enough content to pass validation checks and should be considered valid by the system."
        result = _validate_content(valid_content)
        assert result.is_valid == True
        assert len(result.errors) == 0
        
        # Test invalid content (too short)
        short_content = "Too short"
        result = _validate_content(short_content)
        assert result.is_valid == False
        assert len(result.errors) > 0
        
        # Test content with harmful elements
        harmful_content = "Valid content but with <script>alert('xss')</script> harmful elements."
        result = _validate_content(harmful_content)
        assert result.is_valid == False
        assert result.sanitized_content is not None
        assert "<script>" not in result.sanitized_content