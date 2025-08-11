"""
Investment data collection service for market data and sentiment analysis
"""
import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
import logging
from sqlalchemy.orm import Session
from app.models.finance import MarketData, SentimentAnalysis
from app.core.database import get_db
import os
import json

logger = logging.getLogger(__name__)


class YahooFinanceCollector:
    """Collect market data from Yahoo Finance"""
    
    def __init__(self):
        self.session = None
    
    async def get_stock_data(self, symbol: str, period: str = "1d") -> Optional[Dict[str, Any]]:
        """Get stock data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No data found for symbol: {symbol}")
                return None
            
            latest = hist.iloc[-1]
            info = ticker.info
            
            return {
                "symbol": symbol.upper(),
                "timestamp": datetime.now(),
                "open_price": float(latest['Open']) if pd.notna(latest['Open']) else None,
                "high_price": float(latest['High']) if pd.notna(latest['High']) else None,
                "low_price": float(latest['Low']) if pd.notna(latest['Low']) else None,
                "close_price": float(latest['Close']),
                "volume": int(latest['Volume']) if pd.notna(latest['Volume']) else None,
                "adjusted_close": float(latest['Close']),
                "data_source": "yahoo_finance",
                "company_info": {
                    "name": info.get('longName', ''),
                    "sector": info.get('sector', ''),
                    "industry": info.get('industry', ''),
                    "market_cap": info.get('marketCap', 0),
                    "pe_ratio": info.get('trailingPE', 0),
                    "dividend_yield": info.get('dividendYield', 0)
                }
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    async def get_multiple_stocks(self, symbols: List[str], period: str = "1d") -> List[Dict[str, Any]]:
        """Get data for multiple stocks"""
        results = []
        for symbol in symbols:
            data = await self.get_stock_data(symbol, period)
            if data:
                results.append(data)
        return results
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            
            if hist.empty:
                return []
            
            results = []
            for date, row in hist.iterrows():
                results.append({
                    "symbol": symbol.upper(),
                    "timestamp": date.to_pydatetime(),
                    "open_price": float(row['Open']) if pd.notna(row['Open']) else None,
                    "high_price": float(row['High']) if pd.notna(row['High']) else None,
                    "low_price": float(row['Low']) if pd.notna(row['Low']) else None,
                    "close_price": float(row['Close']),
                    "volume": int(row['Volume']) if pd.notna(row['Volume']) else None,
                    "adjusted_close": float(row['Close']),
                    "data_source": "yahoo_finance"
                })
            
            return results
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return []


class AlphaVantageCollector:
    """Collect data from Alpha Vantage API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        self.session = None
    
    async def _make_request(self, params: Dict[str, str]) -> Optional[Dict]:
        """Make API request to Alpha Vantage"""
        if not self.api_key:
            logger.error("Alpha Vantage API key not provided")
            return None
        
        params['apikey'] = self.api_key
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "Error Message" in data:
                        logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                        return None
                    return data
                else:
                    logger.error(f"Alpha Vantage API request failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error making Alpha Vantage request: {str(e)}")
            return None
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time stock quote"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = await self._make_request(params)
        if not data or 'Global Quote' not in data:
            return None
        
        quote = data['Global Quote']
        
        try:
            return {
                "symbol": symbol.upper(),
                "timestamp": datetime.now(),
                "open_price": float(quote.get('02. open', 0)),
                "high_price": float(quote.get('03. high', 0)),
                "low_price": float(quote.get('04. low', 0)),
                "close_price": float(quote.get('05. price', 0)),
                "volume": int(quote.get('06. volume', 0)),
                "adjusted_close": float(quote.get('05. price', 0)),
                "data_source": "alpha_vantage",
                "change_percent": quote.get('10. change percent', '0%')
            }
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing Alpha Vantage quote data: {str(e)}")
            return None
    
    async def get_news_sentiment(self, symbol: str) -> List[Dict[str, Any]]:
        """Get news sentiment for a symbol"""
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'limit': 50
        }
        
        data = await self._make_request(params)
        if not data or 'feed' not in data:
            return []
        
        results = []
        for article in data['feed']:
            try:
                # Extract sentiment for the specific ticker
                ticker_sentiment = None
                if 'ticker_sentiment' in article:
                    for ticker_data in article['ticker_sentiment']:
                        if ticker_data.get('ticker', '').upper() == symbol.upper():
                            ticker_sentiment = ticker_data
                            break
                
                if ticker_sentiment:
                    sentiment_score = float(ticker_sentiment.get('ticker_sentiment_score', 0))
                    
                    results.append({
                        "symbol": symbol.upper(),
                        "content_type": "news",
                        "sentiment_score": max(-1.0, min(1.0, sentiment_score)),  # Clamp to [-1, 1]
                        "confidence": float(ticker_sentiment.get('ticker_sentiment_label', '0.5').replace('Neutral', '0.5').replace('Positive', '0.8').replace('Negative', '0.8').replace('Bullish', '0.9').replace('Bearish', '0.9')),
                        "timestamp": datetime.now(),
                        "source_url": article.get('url', ''),
                        "content_summary": article.get('summary', '')[:500],  # Limit summary length
                        "entities_mentioned": [symbol.upper()]
                    })
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing news sentiment data: {str(e)}")
                continue
        
        return results
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()


class InvestmentDataService:
    """Main service for collecting and storing investment data"""
    
    def __init__(self):
        self.yahoo_collector = YahooFinanceCollector()
        self.alpha_vantage_collector = AlphaVantageCollector()
    
    async def collect_market_data(self, symbols: List[str], db: Session) -> Dict[str, Any]:
        """Collect and store market data for symbols"""
        results = {
            "success": [],
            "failed": [],
            "total_processed": 0
        }
        
        # Try Yahoo Finance first (free and reliable)
        yahoo_data = await self.yahoo_collector.get_multiple_stocks(symbols)
        
        for data in yahoo_data:
            try:
                market_data = MarketData(
                    symbol=data["symbol"],
                    timestamp=data["timestamp"],
                    open_price=Decimal(str(data["open_price"])) if data["open_price"] else None,
                    high_price=Decimal(str(data["high_price"])) if data["high_price"] else None,
                    low_price=Decimal(str(data["low_price"])) if data["low_price"] else None,
                    close_price=Decimal(str(data["close_price"])),
                    volume=data["volume"],
                    adjusted_close=Decimal(str(data["adjusted_close"])),
                    data_source=data["data_source"]
                )
                
                db.add(market_data)
                results["success"].append(data["symbol"])
                results["total_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error storing market data for {data['symbol']}: {str(e)}")
                results["failed"].append(data["symbol"])
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing market data: {str(e)}")
            db.rollback()
        
        return results
    
    async def collect_sentiment_data(self, symbols: List[str], db: Session) -> Dict[str, Any]:
        """Collect and store sentiment data for symbols"""
        results = {
            "success": [],
            "failed": [],
            "total_processed": 0
        }
        
        for symbol in symbols:
            try:
                # Get news sentiment from Alpha Vantage
                sentiment_data = await self.alpha_vantage_collector.get_news_sentiment(symbol)
                
                for data in sentiment_data:
                    sentiment_analysis = SentimentAnalysis(
                        symbol=data["symbol"],
                        content_type=data["content_type"],
                        sentiment_score=Decimal(str(data["sentiment_score"])),
                        confidence=Decimal(str(data["confidence"])),
                        timestamp=data["timestamp"],
                        source_url=data["source_url"],
                        content_summary=data["content_summary"],
                        entities_mentioned=data["entities_mentioned"]
                    )
                    
                    db.add(sentiment_analysis)
                    results["total_processed"] += 1
                
                results["success"].append(symbol)
                
            except Exception as e:
                logger.error(f"Error collecting sentiment data for {symbol}: {str(e)}")
                results["failed"].append(symbol)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing sentiment data: {str(e)}")
            db.rollback()
        
        return results
    
    async def get_latest_market_data(self, symbol: str, db: Session) -> Optional[MarketData]:
        """Get the latest market data for a symbol"""
        return db.query(MarketData).filter(
            MarketData.symbol == symbol.upper()
        ).order_by(MarketData.timestamp.desc()).first()
    
    async def get_sentiment_summary(self, symbol: str, days: int, db: Session) -> Dict[str, Any]:
        """Get sentiment summary for a symbol over the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        sentiments = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.symbol == symbol.upper(),
            SentimentAnalysis.timestamp >= cutoff_date
        ).all()
        
        if not sentiments:
            return {
                "symbol": symbol.upper(),
                "period_days": days,
                "total_articles": 0,
                "average_sentiment": 0,
                "sentiment_trend": "neutral"
            }
        
        total_sentiment = sum(float(s.sentiment_score) for s in sentiments)
        avg_sentiment = total_sentiment / len(sentiments)
        
        # Determine trend
        if avg_sentiment > 0.1:
            trend = "positive"
        elif avg_sentiment < -0.1:
            trend = "negative"
        else:
            trend = "neutral"
        
        return {
            "symbol": symbol.upper(),
            "period_days": days,
            "total_articles": len(sentiments),
            "average_sentiment": round(avg_sentiment, 4),
            "sentiment_trend": trend,
            "positive_count": len([s for s in sentiments if float(s.sentiment_score) > 0.1]),
            "negative_count": len([s for s in sentiments if float(s.sentiment_score) < -0.1]),
            "neutral_count": len([s for s in sentiments if -0.1 <= float(s.sentiment_score) <= 0.1])
        }
    
    async def close(self):
        """Close all collectors"""
        await self.alpha_vantage_collector.close()


# Global instance
investment_data_service = InvestmentDataService()