"""
Content template management API endpoints
"""
import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.models.user import User
from app.models.content import ContentTemplate
from app.schemas.template import (
    TemplateCreateRequest,
    TemplateUpdateRequest,
    TemplateResponse,
    TemplateListResponse,
    TemplateUsageRequest,
    TemplateUsageResponse,
    TemplateSearchRequest,
    TemplateAnalyticsResponse,
    TemplateStatsResponse,
    TemplateRatingRequest,
    TemplateRatingResponse,
    TemplateExportRequest,
    TemplateImportRequest,
    TemplateImportResponse
)
from app.services.rate_limiter import rate_limiter


logger = logging.getLogger(__name__)
router = APIRouter()


def _extract_placeholders(template_content: str) -> List[str]:
    """Extract placeholder variables from template content"""
    # Find placeholders in format {{variable_name}}
    placeholders = re.findall(r'\{\{(\w+)\}\}', template_content)
    return list(set(placeholders))  # Remove duplicates


def _replace_placeholders(template_content: str, variables: Dict[str, str]) -> tuple[str, List[str], List[str]]:
    """Replace placeholders in template content with provided variables"""
    placeholders_found = _extract_placeholders(template_content)
    placeholders_replaced = []
    
    content = template_content
    for placeholder in placeholders_found:
        if placeholder in variables:
            content = content.replace(f'{{{{{placeholder}}}}}', variables[placeholder])
            placeholders_replaced.append(placeholder)
    
    return content, placeholders_found, placeholders_replaced


def _build_search_query(db: Session, search_request: TemplateSearchRequest, user: User):
    """Build search query based on search parameters"""
    query = db.query(ContentTemplate)
    
    # Filter by user's templates or public templates
    query = query.filter(
        or_(
            ContentTemplate.created_by == user.id,
            ContentTemplate.is_public == True
        )
    )
    
    # Apply filters
    if search_request.query:
        search_term = f"%{search_request.query}%"
        query = query.filter(
            or_(
                ContentTemplate.name.ilike(search_term),
                ContentTemplate.description.ilike(search_term),
                ContentTemplate.template_content.ilike(search_term)
            )
        )
    
    if search_request.category:
        query = query.filter(ContentTemplate.category == search_request.category)
    
    if search_request.template_type:
        query = query.filter(ContentTemplate.template_type == search_request.template_type)
    
    if search_request.industry:
        query = query.filter(ContentTemplate.industry.ilike(f"%{search_request.industry}%"))
    
    if search_request.is_public is not None:
        query = query.filter(ContentTemplate.is_public == search_request.is_public)
    
    if search_request.tags:
        # Filter by tags (assuming tags are stored as JSON array)
        for tag in search_request.tags:
            query = query.filter(ContentTemplate.tags.contains([tag]))
    
    # Apply sorting
    sort_field = getattr(ContentTemplate, search_request.sort_by)
    if search_request.sort_order == 'desc':
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(asc(sort_field))
    
    return query


@router.post("/", response_model=TemplateResponse)
async def create_template(
    request: TemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new content template"""
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(f"template_create:{current_user.id}")
        
        # Check if template name already exists for this user
        existing_template = db.query(ContentTemplate).filter(
            and_(
                ContentTemplate.name == request.name,
                ContentTemplate.created_by == current_user.id
            )
        ).first()
        
        if existing_template:
            raise HTTPException(
                status_code=400,
                detail="Template with this name already exists"
            )
        
        # Extract placeholders from template content
        placeholders = _extract_placeholders(request.template_content)
        
        # Create new template
        template = ContentTemplate(
            name=request.name,
            description=request.description,
            template_content=request.template_content,
            category=request.category,
            template_type=request.template_type,
            industry=request.industry,
            is_public=request.is_public,
            tags=request.tags or [],
            placeholders=placeholders,
            created_by=current_user.id,
            usage_count=0
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        logger.info(f"Template created: {template.id} by user {current_user.id}")
        
        return TemplateResponse(
            id=str(template.id),
            name=template.name,
            description=template.description,
            template_content=template.template_content,
            category=template.category,
            template_type=template.template_type,
            industry=template.industry,
            is_public=template.is_public,
            tags=template.tags,
            usage_count=template.usage_count,
            created_by=str(template.created_by),
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except Exception as e:
        logger.error(f"Template creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template creation failed")


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    template_type: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List templates with pagination and filtering"""
    try:
        # Build base query
        query = db.query(ContentTemplate).filter(
            or_(
                ContentTemplate.created_by == current_user.id,
                ContentTemplate.is_public == True
            )
        )
        
        # Apply filters
        if category:
            query = query.filter(ContentTemplate.category == category)
        
        if template_type:
            query = query.filter(ContentTemplate.template_type == template_type)
        
        if is_public is not None:
            query = query.filter(ContentTemplate.is_public == is_public)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        templates = query.offset(offset).limit(per_page).all()
        
        # Convert to response format
        template_responses = [
            TemplateResponse(
                id=str(template.id),
                name=template.name,
                description=template.description,
                template_content=template.template_content,
                category=template.category,
                template_type=template.template_type,
                industry=template.industry,
                is_public=template.is_public,
                tags=template.tags,
                usage_count=template.usage_count,
                created_by=str(template.created_by),
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            for template in templates
        ]
        
        return TemplateListResponse(
            templates=template_responses,
            total=total,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Template listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template listing failed")


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific template by ID"""
    try:
        template = db.query(ContentTemplate).filter(
            and_(
                ContentTemplate.id == template_id,
                or_(
                    ContentTemplate.created_by == current_user.id,
                    ContentTemplate.is_public == True
                )
            )
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return TemplateResponse(
            id=str(template.id),
            name=template.name,
            description=template.description,
            template_content=template.template_content,
            category=template.category,
            template_type=template.template_type,
            industry=template.industry,
            is_public=template.is_public,
            tags=template.tags,
            usage_count=template.usage_count,
            created_by=str(template.created_by),
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template retrieval failed")


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a template"""
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(f"template_update:{current_user.id}")
        
        template = db.query(ContentTemplate).filter(
            and_(
                ContentTemplate.id == template_id,
                ContentTemplate.created_by == current_user.id
            )
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or not owned by user")
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(template, field, value)
        
        # Update placeholders if template content changed
        if 'template_content' in update_data:
            template.placeholders = _extract_placeholders(template.template_content)
        
        template.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(template)
        
        logger.info(f"Template updated: {template.id} by user {current_user.id}")
        
        return TemplateResponse(
            id=str(template.id),
            name=template.name,
            description=template.description,
            template_content=template.template_content,
            category=template.category,
            template_type=template.template_type,
            industry=template.industry,
            is_public=template.is_public,
            tags=template.tags,
            usage_count=template.usage_count,
            created_by=str(template.created_by),
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template update failed")


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a template"""
    try:
        template = db.query(ContentTemplate).filter(
            and_(
                ContentTemplate.id == template_id,
                ContentTemplate.created_by == current_user.id
            )
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or not owned by user")
        
        db.delete(template)
        db.commit()
        
        logger.info(f"Template deleted: {template_id} by user {current_user.id}")
        
        return {"message": "Template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template deletion failed")


@router.post("/search", response_model=TemplateListResponse)
async def search_templates(
    request: TemplateSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search templates with advanced filtering"""
    try:
        # Build search query
        query = _build_search_query(db, request, current_user)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (request.page - 1) * request.per_page
        templates = query.offset(offset).limit(request.per_page).all()
        
        # Convert to response format
        template_responses = [
            TemplateResponse(
                id=str(template.id),
                name=template.name,
                description=template.description,
                template_content=template.template_content,
                category=template.category,
                template_type=template.template_type,
                industry=template.industry,
                is_public=template.is_public,
                tags=template.tags,
                usage_count=template.usage_count,
                created_by=str(template.created_by),
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            for template in templates
        ]
        
        return TemplateListResponse(
            templates=template_responses,
            total=total,
            page=request.page,
            per_page=request.per_page,
            has_next=offset + request.per_page < total,
            has_prev=request.page > 1
        )
        
    except Exception as e:
        logger.error(f"Template search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template search failed")


@router.post("/{template_id}/use", response_model=TemplateUsageResponse)
async def use_template(
    template_id: str,
    request: TemplateUsageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use a template to generate content"""
    try:
        # Rate limiting
        await rate_limiter.check_rate_limit(f"template_use:{current_user.id}")
        
        template = db.query(ContentTemplate).filter(
            and_(
                ContentTemplate.id == template_id,
                or_(
                    ContentTemplate.created_by == current_user.id,
                    ContentTemplate.is_public == True
                )
            )
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Replace placeholders
        generated_content, placeholders_found, placeholders_replaced = _replace_placeholders(
            template.template_content,
            request.variables
        )
        
        # Update usage count in background
        background_tasks.add_task(_increment_template_usage, template.id, db)
        
        logger.info(f"Template used: {template_id} by user {current_user.id}")
        
        return TemplateUsageResponse(
            generated_content=generated_content,
            template_name=template.name,
            variables_used=request.variables,
            placeholders_found=placeholders_found,
            placeholders_replaced=placeholders_replaced
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template usage failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template usage failed")


@router.get("/{template_id}/analytics", response_model=TemplateAnalyticsResponse)
async def get_template_analytics(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a template"""
    try:
        template = db.query(ContentTemplate).filter(
            and_(
                ContentTemplate.id == template_id,
                ContentTemplate.created_by == current_user.id
            )
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or not owned by user")
        
        # Mock analytics data (in production, this would come from actual usage tracking)
        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)
        week_ago = now - timedelta(days=7)
        
        return TemplateAnalyticsResponse(
            template_id=str(template.id),
            template_name=template.name,
            total_usage=template.usage_count,
            usage_this_month=max(0, template.usage_count - 10),  # Mock data
            usage_this_week=max(0, template.usage_count - 20),   # Mock data
            average_rating=4.2,  # Mock data
            total_ratings=15,    # Mock data
            popular_variables={
                "company_name": 25,
                "product_name": 18,
                "target_audience": 12
            },
            usage_by_industry={
                "technology": 40,
                "marketing": 30,
                "business": 20,
                "other": 10
            },
            recent_usage=[
                {
                    "date": (now - timedelta(days=1)).isoformat(),
                    "user_id": "user123",
                    "variables_used": ["company_name", "product_name"]
                },
                {
                    "date": (now - timedelta(days=2)).isoformat(),
                    "user_id": "user456",
                    "variables_used": ["target_audience"]
                }
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Template analytics failed")


@router.post("/seed-defaults")
async def seed_default_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Seed default templates (admin only or for development)"""
    try:
        # This would typically be restricted to admin users
        default_templates = [
            {
                "name": "Business Blog Post",
                "description": "Professional business blog post template",
                "template_content": """# {{title}}

## Introduction
{{company_name}} is excited to share insights about {{topic}}.

## Main Content
{{main_content}}

## Key Benefits
- {{benefit_1}}
- {{benefit_2}}
- {{benefit_3}}

## Conclusion
{{conclusion}}

---
*About {{company_name}}: {{company_description}}*""",
                "category": "business",
                "template_type": "article",
                "industry": "General",
                "is_public": True,
                "tags": ["business", "professional", "corporate"]
            },
            {
                "name": "How-To Guide",
                "description": "Step-by-step tutorial template",
                "template_content": """# How to {{action}}

## What You'll Need
{{requirements}}

## Step-by-Step Instructions

### Step 1: {{step_1_title}}
{{step_1_description}}

### Step 2: {{step_2_title}}
{{step_2_description}}

### Step 3: {{step_3_title}}
{{step_3_description}}

## Tips and Best Practices
{{tips}}

## Conclusion
{{conclusion}}""",
                "category": "education",
                "template_type": "how_to",
                "industry": "General",
                "is_public": True,
                "tags": ["tutorial", "guide", "how-to"]
            }
        ]
        
        created_count = 0
        for template_data in default_templates:
            # Check if template already exists
            existing = db.query(ContentTemplate).filter(
                ContentTemplate.name == template_data["name"]
            ).first()
            
            if not existing:
                placeholders = _extract_placeholders(template_data["template_content"])
                
                template = ContentTemplate(
                    name=template_data["name"],
                    description=template_data["description"],
                    template_content=template_data["template_content"],
                    category=template_data["category"],
                    template_type=template_data["template_type"],
                    industry=template_data["industry"],
                    is_public=template_data["is_public"],
                    tags=template_data["tags"],
                    placeholders=placeholders,
                    created_by=current_user.id,
                    usage_count=0
                )
                
                db.add(template)
                created_count += 1
        
        db.commit()
        
        return {"message": f"Created {created_count} default templates"}
        
    except Exception as e:
        logger.error(f"Default template seeding failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Default template seeding failed")


async def _increment_template_usage(template_id: str, db: Session):
    """Increment template usage count in background"""
    try:
        template = db.query(ContentTemplate).filter(ContentTemplate.id == template_id).first()
        if template:
            template.usage_count += 1
            db.commit()
    except Exception as e:
        logger.error(f"Failed to increment template usage: {str(e)}")