"""
OpenAI API service wrapper with error handling, retry logic, and token tracking
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.core.config import settings


logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Supported content types for blog generation"""
    ARTICLE = "article"
    HOW_TO = "how_to"
    LISTICLE = "listicle"
    OPINION = "opinion"
    NEWS = "news"
    REVIEW = "review"
    TUTORIAL = "tutorial"


class ContentTone(Enum):
    """Supported content tones"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    FORMAL = "formal"
    FRIENDLY = "friendly"


@dataclass
class TokenUsage:
    """Token usage tracking"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float


@dataclass
class ContentGenerationRequest:
    """Content generation request parameters"""
    topic: str
    content_type: ContentType
    tone: ContentTone
    keywords: List[str] = None
    target_length: int = 1000
    include_seo: bool = True
    industry: str = None
    target_audience: str = None


@dataclass
class GeneratedContent:
    """Generated content response"""
    title: str
    content: str
    meta_description: str
    keywords: List[str]
    seo_suggestions: List[str]
    token_usage: TokenUsage


class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors"""
    pass


class OpenAIService:
    """OpenAI API service wrapper with advanced features"""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise OpenAIServiceError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        
        # Token pricing (per 1K tokens) - update as needed
        self.token_pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }
    
    def _calculate_cost(self, usage: dict) -> float:
        """Calculate estimated cost based on token usage"""
        model_pricing = self.token_pricing.get(self.model, {"input": 0.01, "output": 0.03})
        
        input_cost = (usage.get("prompt_tokens", 0) / 1000) * model_pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1000) * model_pricing["output"]
        
        return input_cost + output_cost
    
    def _get_system_prompt(self, content_type: ContentType, tone: ContentTone, industry: str = None) -> str:
        """Generate system prompt based on content type and tone"""
        base_prompt = f"""You are an expert content writer specializing in creating high-quality blog posts.
        
Content Type: {content_type.value}
Tone: {tone.value}
{f'Industry: {industry}' if industry else ''}

Guidelines:
- Create engaging, well-structured content
- Use proper headings and subheadings
- Include relevant examples and insights
- Optimize for SEO while maintaining readability
- Match the specified tone throughout
- Ensure content is original and valuable
"""
        
        # Content type specific instructions
        type_instructions = {
            ContentType.ARTICLE: "Write a comprehensive article with clear introduction, body, and conclusion.",
            ContentType.HOW_TO: "Create a step-by-step guide with numbered instructions and helpful tips.",
            ContentType.LISTICLE: "Structure as a numbered or bulleted list with detailed explanations for each point.",
            ContentType.OPINION: "Express a clear viewpoint with supporting arguments and evidence.",
            ContentType.NEWS: "Present information in an objective, newsworthy format with key facts upfront.",
            ContentType.REVIEW: "Provide balanced analysis with pros, cons, and recommendations.",
            ContentType.TUTORIAL: "Create detailed instructions with examples and troubleshooting tips."
        }
        
        # Tone specific instructions
        tone_instructions = {
            ContentTone.PROFESSIONAL: "Use formal language, industry terminology, and authoritative voice.",
            ContentTone.CASUAL: "Write in a relaxed, conversational style with everyday language.",
            ContentTone.TECHNICAL: "Include technical details, specifications, and expert-level information.",
            ContentTone.CONVERSATIONAL: "Write as if speaking directly to the reader, use 'you' and questions.",
            ContentTone.FORMAL: "Maintain academic or business writing standards with proper structure.",
            ContentTone.FRIENDLY: "Use warm, approachable language with personal touches and encouragement."
        }
        
        return f"""{base_prompt}
        
{type_instructions.get(content_type, '')}

{tone_instructions.get(tone, '')}

Always respond with a JSON object containing:
- title: Compelling, SEO-optimized title
- content: Full blog post content with proper formatting
- meta_description: 150-160 character meta description
- keywords: Array of relevant SEO keywords
- seo_suggestions: Array of SEO optimization tips
"""
    
    def _create_user_prompt(self, request: ContentGenerationRequest) -> str:
        """Create user prompt from generation request"""
        prompt_parts = [
            f"Topic: {request.topic}",
            f"Target length: approximately {request.target_length} words"
        ]
        
        if request.keywords:
            prompt_parts.append(f"Focus keywords: {', '.join(request.keywords)}")
        
        if request.target_audience:
            prompt_parts.append(f"Target audience: {request.target_audience}")
        
        if request.include_seo:
            prompt_parts.append("Include SEO optimization throughout the content")
        
        return "\n".join(prompt_parts)
    
    async def _make_request_with_retry(
        self,
        messages: List[Dict],
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> ChatCompletion:
        """Make OpenAI request with exponential backoff retry logic"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                return response
                
            except openai.RateLimitError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries exceeded for rate limit")
                    
            except openai.APIError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API error, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries exceeded for API error: {str(e)}")
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in OpenAI request: {str(e)}")
                break
        
        raise OpenAIServiceError(f"Failed to complete request after {max_retries} attempts: {str(last_exception)}")
    
    async def generate_content(self, request: ContentGenerationRequest) -> GeneratedContent:
        """Generate blog content based on request parameters"""
        try:
            system_prompt = self._get_system_prompt(
                request.content_type,
                request.tone,
                request.industry
            )
            user_prompt = self._create_user_prompt(request)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            logger.info(f"Generating content for topic: {request.topic}")
            start_time = time.time()
            
            response = await self._make_request_with_retry(messages)
            
            generation_time = time.time() - start_time
            logger.info(f"Content generated in {generation_time:.2f}s")
            
            # Parse response
            content_data = json.loads(response.choices[0].message.content)
            
            # Calculate token usage and cost
            usage = response.usage
            token_usage = TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                estimated_cost=self._calculate_cost(usage.model_dump())
            )
            
            return GeneratedContent(
                title=content_data.get("title", ""),
                content=content_data.get("content", ""),
                meta_description=content_data.get("meta_description", ""),
                keywords=content_data.get("keywords", []),
                seo_suggestions=content_data.get("seo_suggestions", []),
                token_usage=token_usage
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {str(e)}")
            raise OpenAIServiceError("Invalid response format from OpenAI")
        
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise OpenAIServiceError(f"Content generation failed: {str(e)}")
    
    async def generate_content_stream(
        self,
        request: ContentGenerationRequest
    ) -> AsyncGenerator[str, None]:
        """Generate content with streaming response for real-time updates"""
        try:
            system_prompt = self._get_system_prompt(
                request.content_type,
                request.tone,
                request.industry
            )
            user_prompt = self._create_user_prompt(request)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            logger.info(f"Starting streaming content generation for: {request.topic}")
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming content generation failed: {str(e)}")
            raise OpenAIServiceError(f"Streaming failed: {str(e)}")
    
    async def regenerate_section(
        self,
        original_content: str,
        section_to_regenerate: str,
        instructions: str
    ) -> str:
        """Regenerate a specific section of content while maintaining coherence"""
        try:
            system_prompt = """You are an expert content editor. Your task is to regenerate a specific section of a blog post while maintaining coherence with the rest of the content."""
            
            user_prompt = f"""
Original content:
{original_content}

Section to regenerate:
{section_to_regenerate}

Instructions for regeneration:
{instructions}

Please provide only the regenerated section that will replace the specified section.
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self._make_request_with_retry(messages)
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Section regeneration failed: {str(e)}")
            raise OpenAIServiceError(f"Section regeneration failed: {str(e)}")
    
    async def get_seo_suggestions(self, content: str, target_keywords: List[str]) -> List[str]:
        """Get SEO optimization suggestions for existing content"""
        try:
            system_prompt = """You are an SEO expert. Analyze the provided content and give specific, actionable SEO improvement suggestions."""
            
            user_prompt = f"""
Content to analyze:
{content}

Target keywords: {', '.join(target_keywords)}

Provide specific SEO suggestions as a JSON array of strings.
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self._make_request_with_retry(messages)
            suggestions = json.loads(response.choices[0].message.content)
            
            return suggestions if isinstance(suggestions, list) else []
            
        except Exception as e:
            logger.error(f"SEO analysis failed: {str(e)}")
            raise OpenAIServiceError(f"SEO analysis failed: {str(e)}")


# Global service instance - initialized lazily
openai_service = None

def get_openai_service() -> OpenAIService:
    """Get or create the global OpenAI service instance"""
    global openai_service
    if openai_service is None:
        openai_service = OpenAIService()
    return openai_service