"""
AI-powered content writing service using OpenAI GPT
"""
import openai
from app.config import settings
from typing import Dict, Any

class AIWriter:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
    
    def enhance_content(self, content: str, post_type: str = "blog") -> str:
        """
        Enhance raw content using AI
        """
        prompt = f"""
        Enhance the following {post_type} content:
        - Add engaging headlines
        - Improve readability
        - Add SEO-friendly structure
        - Include relevant metadata
        
        Content:
        {content}
        
        Return enhanced content in markdown format:
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional blog writer and SEO expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"AI enhancement failed: {str(e)}")
    
    def generate_investment_analysis(self, data: Dict[str, Any]) -> str:
        """
        Generate investment analysis content from market data
        """
        prompt = f"""
        Create a comprehensive investment analysis blog post based on this data:
        
        Stock/Asset: {data.get('symbol', 'N/A')}
        Current Price: {data.get('current_price', 'N/A')}
        Price Change: {data.get('price_change', 'N/A')}
        Volume: {data.get('volume', 'N/A')}
        Market Cap: {data.get('market_cap', 'N/A')}
        
        Additional Data: {data.get('additional_info', '')}
        
        Include:
        1. Executive Summary
        2. Technical Analysis
        3. Fundamental Analysis
        4. Risk Assessment
        5. Investment Recommendation
        6. Conclusion
        
        Write in a professional, informative tone suitable for investors.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional financial analyst and investment advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.6
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Investment analysis generation failed: {str(e)}")
    
    def generate_headline(self, content: str) -> str:
        """
        Generate SEO-friendly headline for content
        """
        prompt = f"""
        Generate 3 SEO-friendly, engaging headlines for this content:
        
        {content[:500]}...
        
        Requirements:
        - Under 60 characters
        - Include relevant keywords
        - Engaging and clickable
        - Professional tone
        
        Return only the headlines, numbered 1-3:
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an SEO and content marketing expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            headlines = response.choices[0].message.content.strip().split('\n')
            return headlines[0] if headlines else "Generated Content"
        except Exception as e:
            return "AI-Generated Blog Post"
    
    def generate_meta_description(self, content: str) -> str:
        """
        Generate meta description for SEO
        """
        prompt = f"""
        Create a compelling meta description (150-160 characters) for this content:
        
        {content[:300]}...
        
        Requirements:
        - Exactly 150-160 characters
        - Include main keywords
        - Compelling call-to-action
        - Summarize key value
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an SEO expert specializing in meta descriptions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "Discover insights and analysis in this comprehensive blog post."