"""
Investment blog content generator service
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.finance import (
    MarketData, SentimentAnalysis, InvestmentInsight, 
    InvestmentProfile
)
from app.models.content import BlogPost
from app.services.investment_analyzer import investment_analysis_service
from app.services.investment_data_collector import investment_data_service
import openai
import os

logger = logging.getLogger(__name__)


class InvestmentBlogGenerator:
    """Generate investment-focused blog content"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
    
    async def generate_market_analysis_post(self, symbols: List[str], user_id: str, db: Session) -> Optional[BlogPost]:
        """Generate a comprehensive market analysis blog post"""
        if not self.openai_client:
            logger.error("OpenAI API key not configured")
            return None
        
        # Collect analysis data for all symbols
        analyses = {}
        for symbol in symbols:
            analysis = await investment_analysis_service.analyze_stock(symbol, db, days=30)
            if "error" not in analysis:
                analyses[symbol] = analysis
        
        if not analyses:
            logger.error("No analysis data available for symbols")
            return None
        
        # Generate blog content
        content = await self._create_market_analysis_content(analyses)
        if not content:
            return None
        
        # Create blog post
        blog_post = BlogPost(
            user_id=user_id,
            title=content["title"],
            content=content["body"],
            meta_description=content["meta_description"],
            keywords=content["keywords"],
            status='draft',
            post_type='analysis',
            content_source='ai_investment',
            tone='professional',
            industry='finance',
            word_count=len(content["body"].split()),
            api_data_sources=[f"investment_analysis_{symbol}" for symbol in symbols]
        )
        
        blog_post.calculate_reading_time()
        
        db.add(blog_post)
        db.commit()
        
        return blog_post
    
    async def generate_stock_spotlight_post(self, symbol: str, user_id: str, db: Session) -> Optional[BlogPost]:
        """Generate a detailed stock spotlight post"""
        if not self.openai_client:
            logger.error("OpenAI API key not configured")
            return None
        
        # Get comprehensive analysis
        analysis = await investment_analysis_service.analyze_stock(symbol, db, days=60)
        if "error" in analysis:
            logger.error(f"Analysis error for {symbol}: {analysis['error']}")
            return None
        
        # Get company information
        latest_data = db.query(MarketData).filter(
            MarketData.symbol == symbol.upper()
        ).order_by(desc(MarketData.timestamp)).first()
        
        if not latest_data:
            logger.error(f"No market data found for {symbol}")
            return None
        
        # Generate content
        content = await self._create_stock_spotlight_content(symbol, analysis, latest_data)
        if not content:
            return None
        
        blog_post = BlogPost(
            user_id=user_id,
            title=content["title"],
            content=content["body"],
            meta_description=content["meta_description"],
            keywords=content["keywords"],
            status='draft',
            post_type='spotlight',
            content_source='ai_investment',
            tone='professional',
            industry='finance',
            word_count=len(content["body"].split()),
            api_data_sources=[f"stock_analysis_{symbol}"]
        )
        
        blog_post.calculate_reading_time()
        
        db.add(blog_post)
        db.commit()
        
        return blog_post    asyn
c def generate_sentiment_report_post(self, symbols: List[str], user_id: str, db: Session) -> Optional[BlogPost]:
        """Generate a market sentiment report post"""
        if not self.openai_client:
            logger.error("OpenAI API key not configured")
            return None
        
        # Collect sentiment data
        sentiment_summaries = {}
        for symbol in symbols:
            summary = await investment_data_service.get_sentiment_summary(symbol, 7, db)
            if summary["total_articles"] > 0:
                sentiment_summaries[symbol] = summary
        
        if not sentiment_summaries:
            logger.error("No sentiment data available")
            return None
        
        # Generate content
        content = await self._create_sentiment_report_content(sentiment_summaries)
        if not content:
            return None
        
        blog_post = BlogPost(
            user_id=user_id,
            title=content["title"],
            content=content["body"],
            meta_description=content["meta_description"],
            keywords=content["keywords"],
            status='draft',
            post_type='report',
            content_source='ai_investment',
            tone='professional',
            industry='finance',
            word_count=len(content["body"].split()),
            api_data_sources=[f"sentiment_analysis_{symbol}" for symbol in symbols]
        )
        
        blog_post.calculate_reading_time()
        
        db.add(blog_post)
        db.commit()
        
        return blog_post
    
    async def _create_market_analysis_content(self, analyses: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create market analysis blog content using AI"""
        try:
            # Prepare analysis summary for AI
            analysis_summary = []
            for symbol, data in analyses.items():
                analysis_summary.append(f"""
                {symbol}:
                - Current Price: ${data.get('current_price', 0):.2f}
                - Price Change: {data.get('price_change_percent', 0):.2f}%
                - Technical Trend: {data.get('technical_analysis', {}).get('trend', 'neutral')}
                - Sentiment: {data.get('sentiment_analysis', {}).get('trend', 'neutral')}
                - Recommendation: {data.get('assessment', {}).get('recommendation', 'Hold')}
                - Key Factors: {', '.join(data.get('assessment', {}).get('key_factors', [])[:3])}
                """)
            
            prompt = f"""
            Write a comprehensive market analysis blog post based on the following stock analyses:
            
            {chr(10).join(analysis_summary)}
            
            The blog post should:
            1. Have an engaging title that mentions market analysis
            2. Include an introduction about current market conditions
            3. Analyze each stock with key insights
            4. Provide overall market outlook
            5. Include actionable investment advice
            6. Be 800-1200 words
            7. Use professional but accessible language
            8. Include relevant financial terminology
            
            Format the response as a complete blog post with clear sections.
            """
            
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            blog_content = response.choices[0].message.content.strip()
            
            # Extract title (assume first line is title)
            lines = blog_content.split('\n')
            title = lines[0].replace('#', '').strip()
            body = '\n'.join(lines[1:]).strip()
            
            # Generate meta description
            meta_desc_prompt = f"Write a 150-character SEO meta description for this blog post title: {title}"
            meta_response = await self.openai_client.chat.completions.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": meta_desc_prompt}],
                max_tokens=50,
                temperature=0.5
            )
            
            meta_description = meta_response.choices[0].message.content.strip()[:160]
            
            # Generate keywords
            symbols_list = list(analyses.keys())
            keywords = [
                "market analysis", "stock analysis", "investment insights",
                "financial markets", "trading recommendations"
            ] + [f"{symbol} stock" for symbol in symbols_list[:3]]
            
            return {
                "title": title,
                "body": body,
                "meta_description": meta_description,
                "keywords": keywords
            }
            
        except Exception as e:
            logger.error(f"Error creating market analysis content: {str(e)}")
            return None
    
    async def _create_stock_spotlight_content(self, symbol: str, analysis: Dict[str, Any], market_data: MarketData) -> Optional[Dict[str, Any]]:
        """Create stock spotlight blog content"""
        try:
            prompt = f"""
            Write a detailed stock spotlight blog post for {symbol} based on this analysis:
            
            Current Price: ${analysis.get('current_price', 0):.2f}
            Price Change (30d): {analysis.get('price_change_percent', 0):.2f}%
            Technical Analysis:
            - Trend: {analysis.get('technical_analysis', {}).get('trend', 'neutral')}
            - RSI: {analysis.get('technical_analysis', {}).get('rsi', 50):.1f}
            - Signals: {', '.join(analysis.get('technical_analysis', {}).get('signals', []))}
            
            Sentiment Analysis:
            - Trend: {analysis.get('sentiment_analysis', {}).get('trend', 'neutral')}
            - Average Sentiment: {analysis.get('sentiment_analysis', {}).get('average_sentiment', 0):.3f}
            - Articles Analyzed: {analysis.get('sentiment_analysis', {}).get('total_articles', 0)}
            
            Investment Assessment:
            - Recommendation: {analysis.get('assessment', {}).get('recommendation', 'Hold')}
            - Risk Level: {analysis.get('assessment', {}).get('risk_level', 'medium')}
            - Key Factors: {', '.join(analysis.get('assessment', {}).get('key_factors', []))}
            
            The blog post should:
            1. Have an engaging title featuring the stock symbol
            2. Include company background (you can use general knowledge)
            3. Analyze recent performance and technical indicators
            4. Discuss market sentiment and news impact
            5. Provide investment thesis and recommendation
            6. Include risk considerations
            7. Be 1000-1500 words
            8. Use professional investment language
            
            Format as a complete blog post with clear sections and subheadings.
            """
            
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.7
            )
            
            blog_content = response.choices[0].message.content.strip()
            
            # Extract title
            lines = blog_content.split('\n')
            title = lines[0].replace('#', '').strip()
            body = '\n'.join(lines[1:]).strip()
            
            # Generate meta description
            meta_description = f"Comprehensive analysis of {symbol} stock including technical indicators, sentiment analysis, and investment recommendations."[:160]
            
            # Generate keywords
            keywords = [
                f"{symbol} stock", f"{symbol} analysis", "stock spotlight",
                "investment analysis", "technical analysis", "market sentiment",
                "stock recommendation", "equity research"
            ]
            
            return {
                "title": title,
                "body": body,
                "meta_description": meta_description,
                "keywords": keywords
            }
            
        except Exception as e:
            logger.error(f"Error creating stock spotlight content: {str(e)}")
            return None
    
    async def _create_sentiment_report_content(self, sentiment_summaries: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create sentiment report blog content"""
        try:
            # Prepare sentiment data for AI
            sentiment_data = []
            for symbol, summary in sentiment_summaries.items():
                sentiment_data.append(f"""
                {symbol}:
                - Average Sentiment: {summary.get('average_sentiment', 0):.3f}
                - Trend: {summary.get('sentiment_trend', 'neutral')}
                - Articles Analyzed: {summary.get('total_articles', 0)}
                - Positive/Negative Ratio: {summary.get('positive_count', 0)}/{summary.get('negative_count', 0)}
                """)
            
            prompt = f"""
            Write a market sentiment report blog post based on the following sentiment analysis data:
            
            {chr(10).join(sentiment_data)}
            
            The blog post should:
            1. Have an engaging title about market sentiment
            2. Explain what market sentiment means for investors
            3. Analyze sentiment trends for each stock
            4. Discuss implications for market direction
            5. Provide actionable insights for investors
            6. Include methodology explanation
            7. Be 700-1000 words
            8. Use accessible but professional language
            
            Format as a complete blog post with clear sections.
            """
            
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            blog_content = response.choices[0].message.content.strip()
            
            # Extract title
            lines = blog_content.split('\n')
            title = lines[0].replace('#', '').strip()
            body = '\n'.join(lines[1:]).strip()
            
            # Generate meta description
            meta_description = "Weekly market sentiment analysis covering key stocks and their investor sentiment trends."[:160]
            
            # Generate keywords
            symbols_list = list(sentiment_summaries.keys())
            keywords = [
                "market sentiment", "investor sentiment", "sentiment analysis",
                "market psychology", "trading sentiment", "stock sentiment"
            ] + [f"{symbol} sentiment" for symbol in symbols_list[:3]]
            
            return {
                "title": title,
                "body": body,
                "meta_description": meta_description,
                "keywords": keywords
            }
            
        except Exception as e:
            logger.error(f"Error creating sentiment report content: {str(e)}")
            return None
    
    async def generate_weekly_market_summary(self, user_id: str, db: Session) -> Optional[BlogPost]:
        """Generate a weekly market summary post"""
        # Get top performing and worst performing stocks from the last week
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # This would need to be implemented based on your market data
        # For now, using popular symbols as example
        popular_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        
        return await self.generate_market_analysis_post(popular_symbols, user_id, db)
    
    async def generate_sector_analysis_post(self, sector: str, symbols: List[str], user_id: str, db: Session) -> Optional[BlogPost]:
        """Generate a sector-specific analysis post"""
        if not self.openai_client:
            logger.error("OpenAI API key not configured")
            return None
        
        # Get analysis for all symbols in the sector
        analyses = {}
        for symbol in symbols:
            analysis = await investment_analysis_service.analyze_stock(symbol, db, days=30)
            if "error" not in analysis:
                analyses[symbol] = analysis
        
        if not analyses:
            return None
        
        # Generate sector-specific content
        content = await self._create_sector_analysis_content(sector, analyses)
        if not content:
            return None
        
        blog_post = BlogPost(
            user_id=user_id,
            title=content["title"],
            content=content["body"],
            meta_description=content["meta_description"],
            keywords=content["keywords"],
            status='draft',
            post_type='sector_analysis',
            content_source='ai_investment',
            tone='professional',
            industry='finance',
            word_count=len(content["body"].split()),
            api_data_sources=[f"sector_analysis_{sector}"]
        )
        
        blog_post.calculate_reading_time()
        
        db.add(blog_post)
        db.commit()
        
        return blog_post
    
    async def _create_sector_analysis_content(self, sector: str, analyses: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create sector analysis blog content"""
        try:
            # Prepare sector analysis data
            sector_summary = []
            for symbol, data in analyses.items():
                sector_summary.append(f"""
                {symbol}:
                - Price Change: {data.get('price_change_percent', 0):.2f}%
                - Recommendation: {data.get('assessment', {}).get('recommendation', 'Hold')}
                - Technical Trend: {data.get('technical_analysis', {}).get('trend', 'neutral')}
                - Sentiment: {data.get('sentiment_analysis', {}).get('trend', 'neutral')}
                """)
            
            prompt = f"""
            Write a comprehensive {sector} sector analysis blog post based on the following stock analyses:
            
            {chr(10).join(sector_summary)}
            
            The blog post should:
            1. Have an engaging title about {sector} sector analysis
            2. Provide sector overview and recent trends
            3. Analyze key players in the sector
            4. Discuss sector-specific challenges and opportunities
            5. Compare performance across companies
            6. Provide sector investment outlook
            7. Be 1000-1400 words
            8. Use professional investment language
            
            Format as a complete blog post with clear sections.
            """
            
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2200,
                temperature=0.7
            )
            
            blog_content = response.choices[0].message.content.strip()
            
            # Extract title
            lines = blog_content.split('\n')
            title = lines[0].replace('#', '').strip()
            body = '\n'.join(lines[1:]).strip()
            
            # Generate meta description
            meta_description = f"Comprehensive {sector} sector analysis covering key stocks, trends, and investment opportunities."[:160]
            
            # Generate keywords
            keywords = [
                f"{sector} sector", f"{sector} stocks", f"{sector} analysis",
                "sector analysis", "investment opportunities", "stock comparison"
            ]
            
            return {
                "title": title,
                "body": body,
                "meta_description": meta_description,
                "keywords": keywords
            }
            
        except Exception as e:
            logger.error(f"Error creating sector analysis content: {str(e)}")
            return None


# Global instance
investment_blog_generator = InvestmentBlogGenerator()