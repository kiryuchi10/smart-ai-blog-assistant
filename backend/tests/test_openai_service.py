"""
Unit tests for OpenAI service with mocked responses
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage

from app.services.openai_service import (
    OpenAIService,
    ContentGenerationRequest,
    ContentType,
    ContentTone,
    GeneratedContent,
    TokenUsage,
    OpenAIServiceError
)


@pytest.fixture
def openai_service():
    """Create OpenAI service instance for testing"""
    with patch('app.services.openai_service.settings') as mock_settings:
        mock_settings.openai_api_key = "test-api-key"
        mock_settings.openai_model = "gpt-4"
        mock_settings.openai_max_tokens = 2000
        service = OpenAIService()
        return service


@pytest.fixture
def sample_request():
    """Sample content generation request"""
    return ContentGenerationRequest(
        topic="How to improve website SEO",
        content_type=ContentType.HOW_TO,
        tone=ContentTone.PROFESSIONAL,
        keywords=["SEO", "website optimization", "search rankings"],
        target_length=1000,
        include_seo=True,
        industry="Digital Marketing",
        target_audience="Small business owners"
    )


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    content_data = {
        "title": "How to Improve Your Website SEO: A Complete Guide",
        "content": "# How to Improve Your Website SEO\n\nSEO is crucial for online success...",
        "meta_description": "Learn how to improve your website SEO with proven strategies and techniques.",
        "keywords": ["SEO", "website optimization", "search rankings", "digital marketing"],
        "seo_suggestions": [
            "Include target keywords in title and headings",
            "Optimize meta descriptions for click-through rates",
            "Use internal linking to improve site structure"
        ]
    }
    
    usage = CompletionUsage(
        prompt_tokens=150,
        completion_tokens=800,
        total_tokens=950
    )
    
    message = ChatCompletionMessage(
        role="assistant",
        content=json.dumps(content_data)
    )
    
    choice = Choice(
        index=0,
        message=message,
        finish_reason="stop"
    )
    
    return ChatCompletion(
        id="test-completion-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[choice],
        usage=usage
    )


class TestOpenAIService:
    """Test cases for OpenAI service"""
    
    def test_initialization_without_api_key(self):
        """Test service initialization fails without API key"""
        with patch('app.services.openai_service.settings') as mock_settings:
            mock_settings.openai_api_key = ""
            
            with pytest.raises(OpenAIServiceError, match="OpenAI API key not configured"):
                OpenAIService()
    
    def test_calculate_cost(self, openai_service):
        """Test token cost calculation"""
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300
        }
        
        cost = openai_service._calculate_cost(usage)
        
        # Expected: (100/1000 * 0.03) + (200/1000 * 0.06) = 0.003 + 0.012 = 0.015
        assert cost == 0.015
    
    def test_get_system_prompt(self, openai_service):
        """Test system prompt generation"""
        prompt = openai_service._get_system_prompt(
            ContentType.HOW_TO,
            ContentTone.PROFESSIONAL,
            "Technology"
        )
        
        assert "how_to" in prompt
        assert "professional" in prompt
        assert "Technology" in prompt
        assert "JSON object" in prompt
    
    def test_create_user_prompt(self, openai_service, sample_request):
        """Test user prompt creation"""
        prompt = openai_service._create_user_prompt(sample_request)
        
        assert sample_request.topic in prompt
        assert str(sample_request.target_length) in prompt
        assert "SEO" in prompt
        assert sample_request.target_audience in prompt
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, openai_service, sample_request, mock_openai_response):
        """Test successful content generation"""
        with patch.object(openai_service, '_make_request_with_retry', return_value=mock_openai_response):
            result = await openai_service.generate_content(sample_request)
            
            assert isinstance(result, GeneratedContent)
            assert result.title == "How to Improve Your Website SEO: A Complete Guide"
            assert "SEO is crucial" in result.content
            assert len(result.keywords) == 4
            assert len(result.seo_suggestions) == 3
            assert isinstance(result.token_usage, TokenUsage)
            assert result.token_usage.total_tokens == 950
    
    @pytest.mark.asyncio
    async def test_generate_content_json_parse_error(self, openai_service, sample_request):
        """Test content generation with invalid JSON response"""
        # Mock response with invalid JSON
        invalid_response = MagicMock()
        invalid_response.choices = [MagicMock()]
        invalid_response.choices[0].message.content = "Invalid JSON content"
        invalid_response.usage = CompletionUsage(
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300
        )
        
        with patch.object(openai_service, '_make_request_with_retry', return_value=invalid_response):
            with pytest.raises(OpenAIServiceError, match="Invalid response format"):
                await openai_service.generate_content(sample_request)
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_success(self, openai_service, mock_openai_response):
        """Test successful request without retries"""
        with patch.object(openai_service.client.chat.completions, 'create', return_value=mock_openai_response):
            messages = [{"role": "user", "content": "test"}]
            result = await openai_service._make_request_with_retry(messages)
            
            assert result == mock_openai_response
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_rate_limit(self, openai_service):
        """Test retry logic for rate limit errors"""
        from openai import RateLimitError
        
        # Mock rate limit error then success
        mock_create = AsyncMock()
        mock_create.side_effect = [
            RateLimitError("Rate limit exceeded", response=None, body=None),
            mock_openai_response
        ]
        
        with patch.object(openai_service.client.chat.completions, 'create', mock_create):
            with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up test
                messages = [{"role": "user", "content": "test"}]
                result = await openai_service._make_request_with_retry(messages, max_retries=2)
                
                assert mock_create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_max_retries_exceeded(self, openai_service):
        """Test max retries exceeded scenario"""
        from openai import RateLimitError
        
        mock_create = AsyncMock()
        mock_create.side_effect = RateLimitError("Rate limit exceeded", response=None, body=None)
        
        with patch.object(openai_service.client.chat.completions, 'create', mock_create):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                messages = [{"role": "user", "content": "test"}]
                
                with pytest.raises(OpenAIServiceError, match="Failed to complete request"):
                    await openai_service._make_request_with_retry(messages, max_retries=2)
                
                assert mock_create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_regenerate_section(self, openai_service):
        """Test section regeneration"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Regenerated section content"
        
        with patch.object(openai_service, '_make_request_with_retry', return_value=mock_response):
            result = await openai_service.regenerate_section(
                "Original content",
                "Section to regenerate",
                "Make it more engaging"
            )
            
            assert result == "Regenerated section content"
    
    @pytest.mark.asyncio
    async def test_get_seo_suggestions(self, openai_service):
        """Test SEO suggestions generation"""
        suggestions = [
            "Add more internal links",
            "Optimize image alt tags",
            "Improve page loading speed"
        ]
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(suggestions)
        
        with patch.object(openai_service, '_make_request_with_retry', return_value=mock_response):
            result = await openai_service.get_seo_suggestions(
                "Sample content",
                ["SEO", "optimization"]
            )
            
            assert result == suggestions
            assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_generate_content_stream(self, openai_service, sample_request):
        """Test streaming content generation"""
        # Mock streaming response
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "First chunk"
        
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "Second chunk"
        
        mock_chunk3 = MagicMock()
        mock_chunk3.choices = [MagicMock()]
        mock_chunk3.choices[0].delta.content = None  # End of stream
        
        async def mock_stream():
            yield mock_chunk1
            yield mock_chunk2
            yield mock_chunk3
        
        with patch.object(openai_service.client.chat.completions, 'create', return_value=mock_stream()):
            chunks = []
            async for chunk in openai_service.generate_content_stream(sample_request):
                chunks.append(chunk)
            
            assert chunks == ["First chunk", "Second chunk"]


@pytest.mark.asyncio
async def test_service_integration():
    """Integration test with actual service instance"""
    with patch('app.services.openai_service.settings') as mock_settings:
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4"
        mock_settings.openai_max_tokens = 2000
        
        # Test that service can be imported and initialized
        from app.services.openai_service import openai_service
        assert openai_service is not None
        assert openai_service.model == "gpt-4"