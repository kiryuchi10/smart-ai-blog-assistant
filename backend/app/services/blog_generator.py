"""
AI-powered blog post generation service
"""
import openai
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class BlogGenerator:
    """Service for generating investment blog posts"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
    
    async def generate_investment_blog(self, analyses: List[Dict], topic: str = "Market Analysis") -> Dict:
        """Generate a comprehensive investment blog post"""
        try:
            if not analyses:
                return {"error": "No analysis data provided"}
            
            # Extract key information
            tickers = [analysis.get('ticker', '') for analysis in analyses]
            
            # Generate blog content
            if settings.OPENAI_API_KEY:
                content = await self._generate_ai_blog(analyses, topic)
            else:
                content = self._generate_basic_blog(analyses, topic)
            
            # Generate title
            title = await self._generate_title(tickers, topic)
            
            # Generate summary
            summary = await self._generate_summary(content)
            
            return {
                "title": title,
                "content": content,
                "summary": summary,
                "tickers_analyzed": ",".join(tickers),
                "word_count": len(content.split()),
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating blog post: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_ai_blog(self, analyses: List[Dict], topic: str) -> str:
        """Generate blog content using OpenAI"""
        try:
            # Prepare analysis data for prompt
            analysis_summary = []
            for analysis in analyses:
                ticker = analysis.get('ticker', '')
                stock_data = analysis.get('stock_data', {})
                ai_analysis = analysis.get('ai_analysis', '')
                recommendation = analysis.get('recommendation', 'hold')
                
                analysis_summary.append(f"""
                {ticker} ({stock_data.get('company_name', ticker)}):
                - Current Price: ${stock_data.get('price', 0):.2f}
                - Recommendation: {recommendation.upper()}
                - Analysis: {ai_analysis[:200]}...
                """)
            
            prompt = f"""
            Write a professional investment blog post about {topic} based on the following stock analyses:
            
            {chr(10).join(analysis_summary)}
            
            Structure the blog post with:
            1. Introduction - Brief market overview
            2. Individual Stock Analysis - Key insights for each stock
            3. Market Trends - Overall patterns and themes
            4. Investment Outlook - Forward-looking perspective
            5. Conclusion - Key takeaways and recommendations
            
            Keep the tone professional but accessible. Target length: 800-1200 words.
            Include specific data points and avoid generic statements.
            Add disclaimers about investment risks.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI blog content: {str(e)}")
            return self._generate_basic_blog(analyses, topic)
    
    def _generate_basic_blog(self, analyses: List[Dict], topic: str) -> str:
        """Generate basic blog content without AI"""
        content = f"# {topic} - {datetime.now().strftime('%B %d, %Y')}\n\n"
        
        content += "## Market Overview\n\n"
        content += f"Today's analysis covers {len(analyses)} stocks across various sectors. "
        content += "Market conditions continue to evolve, presenting both opportunities and challenges for investors.\n\n"
        
        content += "## Stock Analysis\n\n"
        
        for analysis in analyses:
            ticker = analysis.get('ticker', '')
            stock_data = analysis.get('stock_data', {})
            technical_data = analysis.get('technical_indicators', {})
            recommendation = analysis.get('recommendation', 'hold')
            
            content += f"### {ticker} - {stock_data.get('company_name', ticker)}\n\n"
            content += f"**Current Price:** ${stock_data.get('price', 0):.2f}\n"
            content += f"**Recommendation:** {recommendation.upper()}\n"
            content += f"**30-Day Change:** {technical_data.get('price_change_pct', 0):.2f}%\n\n"
            
            if technical_data.get('rsi'):
                rsi_interpretation = "overbought" if technical_data['rsi'] > 70 else "oversold" if technical_data['rsi'] < 30 else "neutral"
                content += f"The stock shows {rsi_interpretation} conditions with an RSI of {technical_data['rsi']:.2f}. "
            
            content += f"Based on current technical indicators, we recommend a {recommendation} position.\n\n"
        
        content += "## Investment Outlook\n\n"
        content += "Investors should carefully consider their risk tolerance and investment objectives. "
        content += "Market volatility remains a key factor, and diversification continues to be important.\n\n"
        
        content += "## Disclaimer\n\n"
        content += "This analysis is for informational purposes only and should not be considered as financial advice. "
        content += "Please consult with a qualified financial advisor before making investment decisions.\n"
        
        return content
    
    async def _generate_title(self, tickers: List[str], topic: str) -> str:
        """Generate an engaging title for the blog post"""
        if settings.OPENAI_API_KEY:
            try:
                prompt = f"""
                Generate an engaging, SEO-friendly title for an investment blog post analyzing these stocks: {', '.join(tickers)}.
                Topic: {topic}
                
                The title should be:
                - Professional and informative
                - Include key tickers if space allows
                - Be under 60 characters
                - Attract investor interest
                
                Provide only the title, no explanation.
                """
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50,
                    temperature=0.8
                )
                
                return response.choices[0].message.content.strip().strip('"')
                
            except Exception as e:
                logger.error(f"Error generating AI title: {str(e)}")
        
        # Fallback title generation
        if len(tickers) <= 3:
            return f"{', '.join(tickers)} Analysis - {datetime.now().strftime('%B %Y')}"
        else:
            return f"Market Analysis: {len(tickers)} Stocks - {datetime.now().strftime('%B %Y')}"
    
    async def _generate_summary(self, content: str) -> str:
        """Generate a summary of the blog post"""
        if settings.OPENAI_API_KEY:
            try:
                prompt = f"""
                Create a concise 2-3 sentence summary of this investment blog post:
                
                {content[:1000]}...
                
                The summary should highlight key findings and recommendations.
                """
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.5
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.error(f"Error generating AI summary: {str(e)}")
        
        # Basic summary extraction
        lines = content.split('\n')
        summary_lines = [line for line in lines if line.strip() and not line.startswith('#')][:3]
        return ' '.join(summary_lines)[:200] + "..."