"""
Content generation schemas for API requests and responses
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class ContentTypeEnum(str, Enum):
    """Content type enumeration for API"""
    ARTICLE = "article"
    HOW_TO = "how_to"
    LISTICLE = "listicle"
    OPINION = "opinion"
    NEWS = "news"
    REVIEW = "review"
    TUTORIAL = "tutorial"


class ContentToneEnum(str, Enum):
    """Content tone enumeration for API"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    FORMAL = "formal"
    FRIENDLY = "friendly"


class ContentGenerationRequest(BaseModel):
    """Request schema for content generation"""
    topic: str = Field(..., min_length=5, max_length=200, description="Blog post topic")
    content_type: ContentTypeEnum = Field(default=ContentTypeEnum.ARTICLE, description="Type of content to generate")
    tone: ContentToneEnum = Field(default=ContentToneEnum.PROFESSIONAL, description="Tone of the content")
    keywords: Optional[List[str]] = Field(default=None, description="Target keywords for SEO")
    target_length: int = Field(default=1000, ge=300, le=5000, description="Target word count")
    include_seo: bool = Field(default=True, description="Include SEO optimization")
    industry: Optional[str] = Field(default=None, max_length=100, description="Industry context")
    target_audience: Optional[str] = Field(default=None, max_length=200, description="Target audience description")
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 keywords allowed")
            for keyword in v:
                if len(keyword.strip()) < 2:
                    raise ValueError("Keywords must be at least 2 characters long")
        return v
    
    @validator('topic')
    def validate_topic(cls, v):
        if not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()


class TokenUsageResponse(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float


class ContentGenerationResponse(BaseModel):
    """Response schema for generated content"""
    title: str
    content: str
    meta_description: str
    keywords: List[str]
    seo_suggestions: List[str]
    word_count: int
    reading_time: int  # in minutes
    token_usage: TokenUsageResponse


class ContentRegenerationRequest(BaseModel):
    """Request schema for content section regeneration"""
    original_content: str = Field(..., min_length=100, description="Original blog post content")
    section_to_regenerate: str = Field(..., min_length=10, description="Section to regenerate")
    instructions: str = Field(..., min_length=10, max_length=500, description="Instructions for regeneration")


class ContentRegenerationResponse(BaseModel):
    """Response schema for regenerated content section"""
    regenerated_section: str
    token_usage: TokenUsageResponse


class SEOAnalysisRequest(BaseModel):
    """Request schema for SEO analysis"""
    content: str = Field(..., min_length=100, description="Content to analyze")
    target_keywords: List[str] = Field(..., min_items=1, max_items=10, description="Target keywords")
    
    @validator('target_keywords')
    def validate_keywords(cls, v):
        for keyword in v:
            if len(keyword.strip()) < 2:
                raise ValueError("Keywords must be at least 2 characters long")
        return [keyword.strip() for keyword in v]


class SEOAnalysisResponse(BaseModel):
    """Response schema for SEO analysis"""
    seo_score: int = Field(..., ge=0, le=100, description="SEO score out of 100")
    suggestions: List[str]
    keyword_density: dict = Field(..., description="Keyword density analysis")
    readability_score: float
    token_usage: TokenUsageResponse


class ContentValidationError(BaseModel):
    """Content validation error details"""
    field: str
    message: str
    code: str


class ContentValidationResponse(BaseModel):
    """Content validation response"""
    is_valid: bool
    errors: List[ContentValidationError] = []
    warnings: List[str] = []
    sanitized_content: Optional[str] = None


class StreamingContentChunk(BaseModel):
    """Streaming content chunk"""
    chunk: str
    is_complete: bool = False
    error: Optional[str] = None