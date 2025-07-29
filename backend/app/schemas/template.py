"""
Content template schemas for API requests and responses
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class TemplateCategory(str, Enum):
    """Template category enumeration"""
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    HEALTH = "health"
    EDUCATION = "education"
    LIFESTYLE = "lifestyle"
    FINANCE = "finance"
    MARKETING = "marketing"
    TRAVEL = "travel"
    FOOD = "food"
    GENERAL = "general"


class TemplateType(str, Enum):
    """Template type enumeration"""
    ARTICLE = "article"
    HOW_TO = "how_to"
    LISTICLE = "listicle"
    OPINION = "opinion"
    NEWS = "news"
    REVIEW = "review"
    TUTORIAL = "tutorial"
    CASE_STUDY = "case_study"
    INTERVIEW = "interview"


class TemplateCreateRequest(BaseModel):
    """Request schema for creating a template"""
    name: str = Field(..., min_length=3, max_length=200, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Template description")
    template_content: str = Field(..., min_length=50, description="Template content with placeholders")
    category: TemplateCategory = Field(..., description="Template category")
    template_type: TemplateType = Field(..., description="Template type")
    industry: Optional[str] = Field(None, max_length=100, description="Target industry")
    is_public: bool = Field(default=False, description="Whether template is publicly available")
    tags: Optional[List[str]] = Field(default=None, description="Template tags")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            for tag in v:
                if len(tag.strip()) < 2:
                    raise ValueError("Tags must be at least 2 characters long")
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.strip()


class TemplateUpdateRequest(BaseModel):
    """Request schema for updating a template"""
    name: Optional[str] = Field(None, min_length=3, max_length=200, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Template description")
    template_content: Optional[str] = Field(None, min_length=50, description="Template content")
    category: Optional[TemplateCategory] = Field(None, description="Template category")
    template_type: Optional[TemplateType] = Field(None, description="Template type")
    industry: Optional[str] = Field(None, max_length=100, description="Target industry")
    is_public: Optional[bool] = Field(None, description="Whether template is publicly available")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            for tag in v:
                if len(tag.strip()) < 2:
                    raise ValueError("Tags must be at least 2 characters long")
        return v


class TemplateResponse(BaseModel):
    """Response schema for template data"""
    id: str
    name: str
    description: Optional[str]
    template_content: str
    category: str
    template_type: str
    industry: Optional[str]
    is_public: bool
    tags: List[str]
    usage_count: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Response schema for template list"""
    templates: List[TemplateResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class TemplateUsageRequest(BaseModel):
    """Request schema for using a template"""
    template_id: str = Field(..., description="Template ID to use")
    variables: Dict[str, str] = Field(default={}, description="Variables to replace in template")
    
    @validator('variables')
    def validate_variables(cls, v):
        # Ensure all values are strings
        for key, value in v.items():
            if not isinstance(value, str):
                raise ValueError(f"Variable '{key}' must be a string")
        return v


class TemplateUsageResponse(BaseModel):
    """Response schema for template usage"""
    generated_content: str
    template_name: str
    variables_used: Dict[str, str]
    placeholders_found: List[str]
    placeholders_replaced: List[str]


class TemplateSearchRequest(BaseModel):
    """Request schema for template search"""
    query: Optional[str] = Field(None, description="Search query")
    category: Optional[TemplateCategory] = Field(None, description="Filter by category")
    template_type: Optional[TemplateType] = Field(None, description="Filter by type")
    industry: Optional[str] = Field(None, description="Filter by industry")
    is_public: Optional[bool] = Field(None, description="Filter by public/private")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    sort_by: Optional[str] = Field(default="created_at", description="Sort field")
    sort_order: Optional[str] = Field(default="desc", description="Sort order (asc/desc)")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['created_at', 'updated_at', 'name', 'usage_count']
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(allowed_fields)}")
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()


class TemplateAnalyticsResponse(BaseModel):
    """Response schema for template analytics"""
    template_id: str
    template_name: str
    total_usage: int
    usage_this_month: int
    usage_this_week: int
    average_rating: Optional[float]
    total_ratings: int
    popular_variables: Dict[str, int]
    usage_by_industry: Dict[str, int]
    recent_usage: List[Dict[str, Any]]


class TemplateCategoryStats(BaseModel):
    """Template category statistics"""
    category: str
    template_count: int
    total_usage: int
    popular_templates: List[Dict[str, Any]]


class TemplateStatsResponse(BaseModel):
    """Response schema for template statistics"""
    total_templates: int
    public_templates: int
    private_templates: int
    total_usage: int
    category_stats: List[TemplateCategoryStats]
    most_popular_templates: List[TemplateResponse]
    recent_templates: List[TemplateResponse]


class TemplateRatingRequest(BaseModel):
    """Request schema for rating a template"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")


class TemplateRatingResponse(BaseModel):
    """Response schema for template rating"""
    template_id: str
    user_rating: int
    comment: Optional[str]
    average_rating: float
    total_ratings: int
    created_at: datetime


class TemplateExportRequest(BaseModel):
    """Request schema for template export"""
    template_ids: List[str] = Field(..., min_items=1, max_items=50, description="Template IDs to export")
    format: str = Field(default="json", description="Export format (json, csv)")
    include_usage_stats: bool = Field(default=False, description="Include usage statistics")
    
    @validator('format')
    def validate_format(cls, v):
        if v.lower() not in ['json', 'csv']:
            raise ValueError("Export format must be 'json' or 'csv'")
        return v.lower()


class TemplateImportRequest(BaseModel):
    """Request schema for template import"""
    templates: List[Dict[str, Any]] = Field(..., description="Templates to import")
    overwrite_existing: bool = Field(default=False, description="Overwrite existing templates")
    
    @validator('templates')
    def validate_templates(cls, v):
        if len(v) > 100:
            raise ValueError("Maximum 100 templates can be imported at once")
        
        required_fields = ['name', 'template_content', 'category', 'template_type']
        for i, template in enumerate(v):
            for field in required_fields:
                if field not in template:
                    raise ValueError(f"Template {i+1} missing required field: {field}")
        
        return v


class TemplateImportResponse(BaseModel):
    """Response schema for template import"""
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[Dict[str, str]]
    imported_templates: List[str]  # Template IDs