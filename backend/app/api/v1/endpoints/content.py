"""
Content generation API endpoints
"""
import asyncio
import logging
import re
from typing import List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.content import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    ContentRegenerationRequest,
    ContentRegenerationResponse,
    SEOAnalysisRequest,
    SEOAnalysisResponse,
    ContentValidationResponse,
    StreamingContentChunk
)
from app.services.openai_service import (
    get_openai_service,
    ContentType,
    ContentTone,
    ContentGenerationRequest as ServiceRequest,
    OpenAIServiceError
)
from app.services.rate_limiter import rate_limiter
from app.services.subscription_service import check_usage_limits


logger = logging.getLogger(__name__)
router = APIRouter()


def _map_content_type(api_type: str) -> ContentType:
    """Map API content type to service content type"""
    mapping = {
        "article": ContentType.ARTICLE,
        "how_to": ContentType.HOW_TO,
        "listicle": ContentType.LISTICLE,
        "opinion": ContentType.OPINION,
        "news": ContentType.NEWS,
        "review": ContentType.REVIEW,
        "tutorial": ContentType.TUTORIAL
    }
    return mapping.get(api_type, ContentType.ARTICLE)


def _map_content_tone(api_tone: str) -> ContentTone:
    """Map API content tone to service content tone"""
    mapping = {
        "professional": ContentTone.PROFESSIONAL,
        "casual": ContentTone.CASUAL,
        "technical": ContentTone.TECHNICAL,
        "conversational": ContentTone.CONVERSATIONAL,
        "formal": ContentTone.FORMAL,
        "friendly": ContentTone.FRIENDLY
    }
    return mapping.get(api_tone, ContentTone.PROFESSIONAL)


def _calculate_reading_time(content: str) -> int:
    """Calculate estimated reading time in minutes"""
    # Average reading speed: 200-250 words per minute
    words = len(content.split())
    return max(1, round(words / 225))


def _count_words(content: str) -> int:
    """Count words in content"""
    # Remove HTML tags and count words
    clean_content = re.sub(r'<[^>]+>', '', content)
    return len(clean_content.split())


def _validate_content(content: str) -> ContentValidationResponse:
    """Validate and sanitize content"""
    errors = []
    warnings = []
    
    # Basic validation
    if len(content.strip()) < 100:
        errors.append({
            "field": "content",
            "message": "Content must be at least 100 characters long",
            "code": "CONTENT_TOO_SHORT"
        })
    
    # Check for potentially harmful content
    harmful_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            errors.append({
                "field": "content",
                "message": "Content contains potentially harmful elements",
                "code": "HARMFUL_CONTENT"
            })
            break
    
    # Sanitize content (basic HTML sanitization)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
    
    # Check word count
    word_count = _count_words(content)
    if word_count > 5000:
        warnings.append("Content is very long and may affect readability")
    
    return ContentValidationResponse(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        sanitized_content=sanitized if sanitized != content else None
    )


@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate blog content using AI"""
    # Rate limiting (let HTTPException propagate)
    await rate_limiter.check_rate_limit(f"content_generation:{current_user.id}")
    
    # Check subscription limits
    await check_usage_limits(current_user, db)
    
    try:
        
        # Get OpenAI service
        openai_service = get_openai_service()
        
        # Convert API request to service request
        service_request = ServiceRequest(
            topic=request.topic,
            content_type=_map_content_type(request.content_type),
            tone=_map_content_tone(request.tone),
            keywords=request.keywords or [],
            target_length=request.target_length,
            include_seo=request.include_seo,
            industry=request.industry,
            target_audience=request.target_audience
        )
        
        logger.info(f"Generating content for user {current_user.id}, topic: {request.topic}")
        
        # Generate content
        generated_content = await openai_service.generate_content(service_request)
        
        # Validate content
        validation = _validate_content(generated_content.content)
        if not validation.is_valid:
            logger.warning(f"Generated content validation failed: {validation.errors}")
            # Use sanitized content if available
            content = validation.sanitized_content or generated_content.content
        else:
            content = generated_content.content
        
        # Calculate additional metrics
        word_count = _count_words(content)
        reading_time = _calculate_reading_time(content)
        
        # Update user usage in background
        background_tasks.add_task(
            _update_user_usage,
            current_user.id,
            generated_content.token_usage.total_tokens,
            db
        )
        
        response = ContentGenerationResponse(
            title=generated_content.title,
            content=content,
            meta_description=generated_content.meta_description,
            keywords=generated_content.keywords,
            seo_suggestions=generated_content.seo_suggestions,
            word_count=word_count,
            reading_time=reading_time,
            token_usage={
                "prompt_tokens": generated_content.token_usage.prompt_tokens,
                "completion_tokens": generated_content.token_usage.completion_tokens,
                "total_tokens": generated_content.token_usage.total_tokens,
                "estimated_cost": generated_content.token_usage.estimated_cost
            }
        )
        
        logger.info(f"Content generated successfully for user {current_user.id}")
        return response
        
    except OpenAIServiceError as e:
        logger.error(f"OpenAI service error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Content generation service unavailable: {str(e)}")
    
    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Content generation failed")


@router.post("/generate/stream")
async def generate_content_stream(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate blog content with streaming response"""
    # Rate limiting (let HTTPException propagate)
    await rate_limiter.check_rate_limit(f"content_generation:{current_user.id}")
    
    # Check subscription limits
    await check_usage_limits(current_user, db)
    
    try:
        
        # Get OpenAI service
        openai_service = get_openai_service()
        
        # Convert API request to service request
        service_request = ServiceRequest(
            topic=request.topic,
            content_type=_map_content_type(request.content_type),
            tone=_map_content_tone(request.tone),
            keywords=request.keywords or [],
            target_length=request.target_length,
            include_seo=request.include_seo,
            industry=request.industry,
            target_audience=request.target_audience
        )
        
        async def generate_stream():
            try:
                async for chunk in openai_service.generate_content_stream(service_request):
                    chunk_data = StreamingContentChunk(chunk=chunk)
                    yield f"data: {chunk_data.json()}\n\n"
                
                # Send completion signal
                completion_data = StreamingContentChunk(chunk="", is_complete=True)
                yield f"data: {completion_data.json()}\n\n"
                
            except Exception as e:
                error_data = StreamingContentChunk(chunk="", error=str(e))
                yield f"data: {error_data.json()}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming content generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Streaming content generation failed")


@router.post("/regenerate", response_model=ContentRegenerationResponse)
async def regenerate_content_section(
    request: ContentRegenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate a specific section of content"""
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(f"content_regeneration:{current_user.id}")
        
        # Get OpenAI service
        openai_service = get_openai_service()
        
        logger.info(f"Regenerating content section for user {current_user.id}")
        
        # Regenerate section
        regenerated_section = await openai_service.regenerate_section(
            request.original_content,
            request.section_to_regenerate,
            request.instructions
        )
        
        # Validate regenerated content
        validation = _validate_content(regenerated_section)
        if not validation.is_valid:
            logger.warning(f"Regenerated content validation failed: {validation.errors}")
            regenerated_section = validation.sanitized_content or regenerated_section
        
        # Mock token usage for regeneration (would be tracked in real implementation)
        token_usage = {
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300,
            "estimated_cost": 0.01
        }
        
        response = ContentRegenerationResponse(
            regenerated_section=regenerated_section,
            token_usage=token_usage
        )
        
        logger.info(f"Content section regenerated successfully for user {current_user.id}")
        return response
        
    except OpenAIServiceError as e:
        logger.error(f"OpenAI service error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Content regeneration service unavailable: {str(e)}")
    
    except Exception as e:
        logger.error(f"Content regeneration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Content regeneration failed")


@router.post("/analyze-seo", response_model=SEOAnalysisResponse)
async def analyze_seo(
    request: SEOAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze content for SEO optimization"""
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(f"seo_analysis:{current_user.id}")
        
        # Get OpenAI service
        openai_service = get_openai_service()
        
        logger.info(f"Analyzing SEO for user {current_user.id}")
        
        # Get SEO suggestions
        suggestions = await openai_service.get_seo_suggestions(
            request.content,
            request.target_keywords
        )
        
        # Calculate keyword density
        content_words = request.content.lower().split()
        total_words = len(content_words)
        keyword_density = {}
        
        for keyword in request.target_keywords:
            keyword_lower = keyword.lower()
            count = content_words.count(keyword_lower)
            density = (count / total_words) * 100 if total_words > 0 else 0
            keyword_density[keyword] = {
                "count": count,
                "density": round(density, 2)
            }
        
        # Calculate basic SEO score
        seo_score = _calculate_seo_score(request.content, request.target_keywords)
        
        # Calculate readability score (simplified Flesch Reading Ease)
        readability_score = _calculate_readability_score(request.content)
        
        # Mock token usage
        token_usage = {
            "prompt_tokens": 150,
            "completion_tokens": 100,
            "total_tokens": 250,
            "estimated_cost": 0.005
        }
        
        response = SEOAnalysisResponse(
            seo_score=seo_score,
            suggestions=suggestions,
            keyword_density=keyword_density,
            readability_score=readability_score,
            token_usage=token_usage
        )
        
        logger.info(f"SEO analysis completed for user {current_user.id}")
        return response
        
    except OpenAIServiceError as e:
        logger.error(f"OpenAI service error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"SEO analysis service unavailable: {str(e)}")
    
    except Exception as e:
        logger.error(f"SEO analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="SEO analysis failed")


@router.post("/validate", response_model=ContentValidationResponse)
async def validate_content(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Validate and sanitize content"""
    try:
        content = request.get("content", "")
        validation = _validate_content(content)
        return validation
        
    except Exception as e:
        logger.error(f"Content validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Content validation failed")


def _calculate_seo_score(content: str, keywords: List[str]) -> int:
    """Calculate basic SEO score"""
    score = 0
    content_lower = content.lower()
    
    # Check title (assuming first line is title)
    lines = content.split('\n')
    title = lines[0] if lines else ""
    title_lower = title.lower()
    
    # Title contains keywords (30 points)
    for keyword in keywords:
        if keyword.lower() in title_lower:
            score += 30 / len(keywords)
    
    # Content length (20 points)
    word_count = len(content.split())
    if 300 <= word_count <= 2000:
        score += 20
    elif word_count > 2000:
        score += 10
    
    # Keyword density (25 points)
    total_words = len(content_lower.split())
    for keyword in keywords:
        count = content_lower.count(keyword.lower())
        density = (count / total_words) * 100 if total_words > 0 else 0
        if 1 <= density <= 3:  # Optimal keyword density
            score += 25 / len(keywords)
        elif density > 0:
            score += 10 / len(keywords)
    
    # Headings (15 points)
    if re.search(r'#+ ', content):
        score += 15
    
    # Meta description length (10 points)
    if 120 <= len(content) <= 160:
        score += 10
    
    return min(100, int(score))


def _calculate_readability_score(content: str) -> float:
    """Calculate simplified readability score"""
    sentences = len(re.split(r'[.!?]+', content))
    words = len(content.split())
    syllables = sum(_count_syllables(word) for word in content.split())
    
    if sentences == 0 or words == 0:
        return 0.0
    
    # Simplified Flesch Reading Ease formula
    score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
    return max(0.0, min(100.0, score))


def _count_syllables(word: str) -> int:
    """Count syllables in a word (simplified)"""
    word = word.lower().strip(".,!?;:")
    if not word:
        return 0
    
    vowels = "aeiouy"
    syllable_count = 0
    prev_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            syllable_count += 1
        prev_was_vowel = is_vowel
    
    # Handle silent e
    if word.endswith('e') and syllable_count > 1:
        syllable_count -= 1
    
    return max(1, syllable_count)


async def _update_user_usage(user_id: str, tokens_used: int, db: Session):
    """Update user token usage in background"""
    try:
        # This would update user usage statistics
        # Implementation depends on your user model and tracking requirements
        logger.info(f"Updated usage for user {user_id}: {tokens_used} tokens")
    except Exception as e:
        logger.error(f"Failed to update user usage: {str(e)}")