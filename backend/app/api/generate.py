"""
API-based content generation endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_writer import AIWriter
from app.services.visualizer import Visualizer
from app.tasks.post_task import generate_api_post_async

router = APIRouter()

class GenerateRequest(BaseModel):
    topic: str
    post_type: str = "investment"  # investment, review, tutorial
    data_source: str = "yahoo"     # yahoo, alpha_vantage
    symbols: list = []

@router.post("/investment-post")
async def generate_investment_post(request: GenerateRequest):
    """
    Generate investment analysis post using API data
    """
    try:
        task = generate_api_post_async.delay(
            topic=request.topic,
            post_type=request.post_type,
            data_source=request.data_source,
            symbols=request.symbols
        )
        
        return {
            "message": "Investment post generation started",
            "task_id": task.id,
            "topic": request.topic
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/product-review")
async def generate_product_review(request: GenerateRequest):
    """
    Generate product review post
    """
    try:
        # Implementation for product review generation
        return {
            "message": "Product review generation started",
            "topic": request.topic
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_templates():
    """
    Get available post templates
    """
    return {
        "templates": [
            {"name": "investment", "description": "Investment analysis template"},
            {"name": "review", "description": "Product review template"},
            {"name": "tutorial", "description": "Tutorial template"}
        ]
    }