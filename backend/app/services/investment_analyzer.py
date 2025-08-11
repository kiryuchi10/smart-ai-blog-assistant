"""
Investment analysis service using AI
"""
import openai
from typing import Dict, List, Optional
import json
import logging
from app.core.config import settings
from app.services.yahoo_finance_service import YahooFinanceService

logger = logging.getLogger(__name__)

class InvestmentAnalyzer:
    """AI-powered investment analysis service"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        self.yahoo_service = YahooFinanceService()
    
    async def analyze_stock(self, ticker: str) -> Optional[Dict]:
        """Perform comprehensive stock analysis"""
        try:
            # Get stock data and technical indicators
            stock_data = await self.yahoo_service.get_stock_data(ticker)
            technical_data = await self.yahoo_service.calculate_technical_indicators(ticker)
            
            if not stock_data or not technical_data:
                return None
            
            # Combine data for analysis
            analysis_data = {**stock_data, **technical_data}
            
            # Generate AI analysis
            ai_analysis = await self._generate_ai_analysis(ticker, analysis_data)
            
            return {
                "ticker": ticker,
                "stock_data": stock_data,
                "technical_indicators": technical_data,
                "ai_analysis": ai_analysis,
                "recommendation": self._determine_recommendation(technical_data),
                "confidence_score": self._calculate_confidence_score(technical_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing stock {ticker}: {str(e)}")
            return None
    
    async def _generate_ai_analysis(self, ticker: str, data: Dict) -> str:
        """Generate AI-powered analysis using OpenAI"""
        if not settings.OPENAI_API_KEY:
            return self._generate_basic_analysis(ticker, data)
        
        try:
            prompt = f"""
            Analyze the following stock data for {ticker} and provide a concise investment analysis:
            
            Company: {data.get('company_name', ticker)}
            Current Price: ${data.get('price', 0):.2f}
            Market Cap: ${data.get('market_cap', 0):,.0f}
            P/E Ratio: {data.get('pe_ratio', 0):.2f}
            52-Week High: ${data.get('fifty_two_week_high', 0):.2f}
            52-Week Low: ${data.get('fifty_two_week_low', 0):.2f}
            RSI: {data.get('rsi', 0):.2f}
            Price Change (30d): {data.get('price_change_pct', 0):.2f}%
            
            Provide a 2-3 paragraph analysis covering:
            1. Current market position and valuation
            2. Technical indicators and momentum
            3. Key risks and opportunities
            
            Keep the analysis professional and objective.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {str(e)}")
            return self._generate_basic_analysis(ticker, data)
    
    def _generate_basic_analysis(self, ticker: str, data: Dict) -> str:
        """Generate basic analysis without AI"""
        price = data.get('price', 0)
        pe_ratio = data.get('pe_ratio', 0)
        rsi = data.get('rsi', 50)
        price_change = data.get('price_change_pct', 0)
        
        analysis = f"""
        {ticker} is currently trading at ${price:.2f}. The stock has shown a {price_change:.2f}% change over the past 30 days.
        
        With a P/E ratio of {pe_ratio:.2f}, the stock appears {'overvalued' if pe_ratio > 25 else 'reasonably valued' if pe_ratio > 15 else 'undervalued'} 
        relative to earnings. The RSI of {rsi:.2f} suggests the stock is {'overbought' if rsi > 70 else 'oversold' if rsi < 30 else 'in neutral territory'}.
        
        Technical indicators show {'bullish' if price_change > 5 else 'bearish' if price_change < -5 else 'mixed'} momentum. 
        Investors should consider market conditions and company fundamentals before making investment decisions.
        """
        
        return analysis.strip()
    
    def _determine_recommendation(self, technical_data: Dict) -> str:
        """Determine buy/sell/hold recommendation based on technical indicators"""
        rsi = technical_data.get('rsi', 50)
        price_change = technical_data.get('price_change_pct', 0)
        sma_5 = technical_data.get('sma_5', 0)
        sma_20 = technical_data.get('sma_20', 0)
        current_price = technical_data.get('current_price', 0)
        
        score = 0
        
        # RSI scoring
        if rsi < 30:
            score += 2  # Oversold - bullish
        elif rsi > 70:
            score -= 2  # Overbought - bearish
        
        # Price change scoring
        if price_change > 10:
            score += 1
        elif price_change < -10:
            score -= 1
        
        # Moving average scoring
        if sma_5 and sma_20 and current_price:
            if sma_5 > sma_20 and current_price > sma_5:
                score += 1  # Uptrend
            elif sma_5 < sma_20 and current_price < sma_5:
                score -= 1  # Downtrend
        
        if score >= 2:
            return "buy"
        elif score <= -2:
            return "sell"
        else:
            return "hold"
    
    def _calculate_confidence_score(self, technical_data: Dict) -> float:
        """Calculate confidence score for the recommendation"""
        # Simple confidence calculation based on data availability and consistency
        available_indicators = sum([
            1 for key in ['rsi', 'sma_5', 'sma_20', 'price_change_pct'] 
            if technical_data.get(key) is not None
        ])
        
        base_confidence = available_indicators / 4.0  # 0.0 to 1.0
        
        # Adjust based on RSI extremes (higher confidence at extremes)
        rsi = technical_data.get('rsi', 50)
        if rsi < 20 or rsi > 80:
            base_confidence += 0.2
        elif rsi < 30 or rsi > 70:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)