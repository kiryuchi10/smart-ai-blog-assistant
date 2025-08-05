"""
Comment analysis and optimization endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.comment_analyzer import CommentAnalyzer
from app.tasks.optimize_task import analyze_comments_async

router = APIRouter()

class OptimizeRequest(BaseModel):
    post_url: str
    post_id: str = None

@router.post("/analyze-comments")
async def analyze_comments(request: OptimizeRequest):
    """
    Analyze comments and suggest optimizations
    """
    try:
        task = analyze_comments_async.delay(
            post_url=request.post_url,
            post_id=request.post_id
        )
        
        return {
            "message": "Comment analysis started",
            "task_id": task.id,
            "post_url": request.post_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions/{post_id}")
async def get_optimization_suggestions(post_id: str):
    """
    Get optimization suggestions for a post
    """
    try:
        # Implementation for getting suggestions
        return {
            "post_id": post_id,
            "suggestions": [
                {
                    "type": "content_improvement",
                    "description": "Add more technical details based on reader questions",
                    "priority": "high"
                },
                {
                    "type": "follow_up_post",
                    "description": "Create follow-up post about advanced strategies",
                    "priority": "medium"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply-suggestions")
async def apply_suggestions(post_id: str, suggestion_ids: list):
    """
    Apply selected optimization suggestions
    """
    try:
        # Implementation for applying suggestions
        return {
            "message": "Suggestions applied successfully",
            "post_id": post_id,
            "applied_suggestions": suggestion_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))