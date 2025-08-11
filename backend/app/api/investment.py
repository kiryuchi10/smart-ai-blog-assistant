"""
Investment analysis and blog generation API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.investment import StockData, MarketAnalysis, BlogPost
from app.services.investment_analyzer import InvestmentAnalyzer
from app.services.blog_generator import BlogGenerator

router = APIRouter(prefix="/investment", tags=["investment"])

# Initialize services
analyzer = InvestmentAnalyzer()
blog_generator = BlogGenerator()

@router.get("/stocks/{ticker}")
async def get_stock_analysis(ticker: str, db: Session = Depends(get_db)):
    """Get comprehensive analysis for a single stock"""
    try:
        analysis = await analyzer.analyze_stock(ticker.upper())
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Could not analyze stock {ticker}")
        
        # Save stock data to database
        stock_data = StockData(**analysis['stock_data'])
        db.add(stock_data)
        
        # Save analysis to database
        market_analysis = MarketAnalysis(
            ticker=ticker.upper(),
            analysis_type="comprehensive",
            analysis_data=json.dumps(analysis),
            recommendation=analysis['recommendation'],
            confidence_score=analysis['confidence_score']
        )
        db.add(market_analysis)
        db.commit()
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stocks")
async def get_multiple_stocks_analysis(
    tickers: str = None, 
    db: Session = Depends(get_db)
):
    """Get analysis for multiple stocks"""
    try:
        if not tickers:
            ticker_list = settings.DEFAULT_TICKERS
        else:
            ticker_list = [t.strip().upper() for t in tickers.split(',')]
        
        analyses = []
        for ticker in ticker_list:
            analysis = await analyzer.analyze_stock(ticker)
            if analysis:
                analyses.append(analysis)
                
                # Save to database
                stock_data = StockData(**analysis['stock_data'])
                db.add(stock_data)
                
                market_analysis = MarketAnalysis(
                    ticker=ticker,
                    analysis_type="comprehensive",
                    analysis_data=json.dumps(analysis),
                    recommendation=analysis['recommendation'],
                    confidence_score=analysis['confidence_score']
                )
                db.add(market_analysis)
        
        db.commit()
        
        return {
            "analyses": analyses,
            "total_stocks": len(analyses),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/blog/generate")
async def generate_investment_blog(
    tickers: Optional[str] = None,
    topic: str = "Market Analysis",
    db: Session = Depends(get_db)
):
    """Generate an investment blog post based on stock analysis"""
    try:
        # Get stock analyses
        if not tickers:
            ticker_list = settings.DEFAULT_TICKERS
        else:
            ticker_list = [t.strip().upper() for t in tickers.split(',')]
        
        analyses = []
        for ticker in ticker_list:
            analysis = await analyzer.analyze_stock(ticker)
            if analysis:
                analyses.append(analysis)
        
        if not analyses:
            raise HTTPException(status_code=400, detail="No valid stock analyses available")
        
        # Generate blog post
        blog_data = await blog_generator.generate_investment_blog(analyses, topic)
        
        if "error" in blog_data:
            raise HTTPException(status_code=500, detail=blog_data["error"])
        
        # Save blog post to database
        blog_post = BlogPost(
            title=blog_data['title'],
            content=blog_data['content'],
            summary=blog_data['summary'],
            tickers_analyzed=blog_data['tickers_analyzed'],
            word_count=blog_data['word_count']
        )
        db.add(blog_post)
        db.commit()
        db.refresh(blog_post)
        
        return {
            "blog_post": blog_data,
            "blog_id": blog_post.id,
            "analyses_used": len(analyses)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blog/posts")
async def get_blog_posts(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get list of generated blog posts"""
    try:
        posts = db.query(BlogPost).offset(offset).limit(limit).all()
        
        return {
            "posts": [
                {
                    "id": post.id,
                    "title": post.title,
                    "summary": post.summary,
                    "tickers_analyzed": post.tickers_analyzed,
                    "word_count": post.word_count,
                    "created_at": post.created_at,
                    "is_published": post.is_published
                }
                for post in posts
            ],
            "total": len(posts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blog/posts/{post_id}")
async def get_blog_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific blog post"""
    try:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        
        if not post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "summary": post.summary,
            "tickers_analyzed": post.tickers_analyzed,
            "word_count": post.word_count,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "is_published": post.is_published
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/overview")
async def get_market_overview(db: Session = Depends(get_db)):
    """Get overall market overview based on recent analyses"""
    try:
        # Get recent analyses
        recent_analyses = db.query(MarketAnalysis).order_by(
            MarketAnalysis.created_at.desc()
        ).limit(20).all()
        
        if not recent_analyses:
            return {"message": "No recent market data available"}
        
        # Calculate market sentiment
        recommendations = [analysis.recommendation for analysis in recent_analyses]
        buy_count = recommendations.count('buy')
        sell_count = recommendations.count('sell')
        hold_count = recommendations.count('hold')
        
        total = len(recommendations)
        sentiment = {
            "bullish_percentage": (buy_count / total) * 100,
            "bearish_percentage": (sell_count / total) * 100,
            "neutral_percentage": (hold_count / total) * 100
        }
        
        # Get average confidence
        avg_confidence = sum(analysis.confidence_score for analysis in recent_analyses) / total
        
        return {
            "market_sentiment": sentiment,
            "average_confidence": avg_confidence,
            "total_analyses": total,
            "last_updated": recent_analyses[0].created_at if recent_analyses else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))