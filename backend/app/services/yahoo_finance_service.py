"""
Yahoo Finance data collection service
"""
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class YahooFinanceService:
    """Service for collecting financial data from Yahoo Finance"""
    
    def __init__(self):
        self.session = None
    
    async def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Get current stock data for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get current price and basic metrics
            stock_data = {
                "ticker": ticker,
                "price": info.get("currentPrice", 0),
                "volume": info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
                "company_name": info.get("longName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown")
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    async def get_historical_data(self, ticker: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get historical price data"""
        try:
            stock = yf.Ticker(ticker)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            hist = stock.history(start=start_date, end=end_date)
            return hist
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
            return None
    
    async def get_multiple_stocks(self, tickers: List[str]) -> Dict[str, Dict]:
        """Get data for multiple stocks"""
        results = {}
        
        for ticker in tickers:
            data = await self.get_stock_data(ticker)
            if data:
                results[ticker] = data
        
        return results
    
    async def calculate_technical_indicators(self, ticker: str, days: int = 30) -> Optional[Dict]:
        """Calculate basic technical indicators"""
        try:
            hist_data = await self.get_historical_data(ticker, days)
            if hist_data is None or hist_data.empty:
                return None
            
            # Calculate simple moving averages
            hist_data['SMA_5'] = hist_data['Close'].rolling(window=5).mean()
            hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
            
            # Calculate RSI (simplified)
            delta = hist_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Get latest values
            latest = hist_data.iloc[-1]
            
            indicators = {
                "current_price": float(latest['Close']),
                "sma_5": float(latest['SMA_5']) if not pd.isna(latest['SMA_5']) else None,
                "sma_20": float(latest['SMA_20']) if not pd.isna(latest['SMA_20']) else None,
                "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
                "volume_avg": float(hist_data['Volume'].mean()),
                "price_change_pct": float(((latest['Close'] - hist_data['Close'].iloc[0]) / hist_data['Close'].iloc[0]) * 100)
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {ticker}: {str(e)}")
            return None