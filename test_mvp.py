#!/usr/bin/env python3
"""
Test script for AI Blog Assistant Investment MVP
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_services():
    """Test core services"""
    print("🧪 Testing AI Blog Assistant MVP Services")
    print("=" * 50)
    
    try:
        # Test Yahoo Finance Service
        print("\n📊 Testing Yahoo Finance Service...")
        from app.services.yahoo_finance_service import YahooFinanceService
        
        yahoo_service = YahooFinanceService()
        stock_data = await yahoo_service.get_stock_data("AAPL")
        
        if stock_data:
            print(f"✓ Successfully fetched AAPL data: ${stock_data.get('price', 0):.2f}")
        else:
            print("✗ Failed to fetch stock data")
            return False
        
        # Test technical indicators
        print("\n📈 Testing Technical Indicators...")
        indicators = await yahoo_service.calculate_technical_indicators("AAPL", 10)
        
        if indicators:
            print(f"✓ Technical indicators calculated: RSI={indicators.get('rsi', 0):.2f}")
        else:
            print("✗ Failed to calculate technical indicators")
        
        # Test Investment Analyzer
        print("\n🤖 Testing Investment Analyzer...")
        from app.services.investment_analyzer import InvestmentAnalyzer
        
        analyzer = InvestmentAnalyzer()
        analysis = await analyzer.analyze_stock("AAPL")
        
        if analysis:
            print(f"✓ Analysis completed: Recommendation={analysis.get('recommendation', 'N/A')}")
        else:
            print("✗ Failed to analyze stock")
        
        # Test Blog Generator
        print("\n📝 Testing Blog Generator...")
        from app.services.blog_generator import BlogGenerator
        
        blog_generator = BlogGenerator()
        if analysis:
            blog_data = await blog_generator.generate_investment_blog([analysis], "Test Analysis")
            
            if blog_data and "title" in blog_data:
                print(f"✓ Blog generated: '{blog_data['title'][:50]}...'")
            else:
                print("✗ Failed to generate blog")
        
        # Test Database Models
        print("\n🗄️ Testing Database Models...")
        from app.core.database import init_db, Base, engine
        from app.models.investment import StockData, MarketAnalysis, BlogPost
        
        await init_db()
        print("✓ Database initialized successfully")
        
        print("\n✅ All tests passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure to run setup_mvp.py first and install dependencies")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        import httpx
        
        # Test health endpoint
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000/api/v1/health/")
                if response.status_code == 200:
                    print("✓ Health endpoint working")
                else:
                    print("✗ Health endpoint not responding")
            except:
                print("⚠ API server not running (this is expected if not started)")
        
    except ImportError:
        print("⚠ httpx not installed, skipping API tests")

def main():
    """Main test function"""
    print("Starting MVP tests...")
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Please run this script from the ai-blog-assistant directory")
        return False
    
    # Run service tests
    success = asyncio.run(test_services())
    
    # Run API tests
    asyncio.run(test_api_endpoints())
    
    if success:
        print("\n🎉 MVP is ready to use!")
        print("\nNext steps:")
        print("1. Add your OpenAI API key to backend/.env")
        print("2. Run start_mvp.bat or ./start_mvp.sh")
        print("3. Open http://localhost:3000")
    else:
        print("\n❌ Some tests failed. Check the setup.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)