#!/usr/bin/env python3
"""
Setup script for integrating investment intelligence features into AI Blog Assistant
"""

import os
import sys
import subprocess
from pathlib import Path

def print_step(step_num, description):
    """Print a formatted step"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\nRunning: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        print(f"✅ {description} exists")
        return True
    else:
        print(f"❌ {description} not found")
        return False

def update_env_file():
    """Update .env file with investment-related environment variables"""
    env_path = Path("ai-blog-assistant/backend/.env")
    env_example_path = Path("ai-blog-assistant/backend/.env.example")
    
    # Read existing .env or create from example
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
    elif env_example_path.exists():
        with open(env_example_path, 'r') as f:
            env_content = f.read()
    else:
        env_content = ""
    
    # Add investment-related variables if not present
    investment_vars = [
        "\n# Investment Intelligence Configuration",
        "ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here",
        "OPENAI_API_KEY=your_openai_api_key_here",
        "INVESTMENT_DATA_UPDATE_INTERVAL=3600  # seconds",
        "ENABLE_INVESTMENT_FEATURES=true"
    ]
    
    for var in investment_vars:
        if var.split('=')[0] not in env_content:
            env_content += f"\n{var}"
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ Environment variables updated")
    print("\n📝 Please update the following in your .env file:")
    print("   - ALPHA_VANTAGE_API_KEY: Get from https://www.alphavantage.co/support/#api-key")
    print("   - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys")

def main():
    """Main setup function"""
    print("🚀 AI Blog Assistant - Investment Intelligence Integration Setup")
    print("This script will integrate finance and investment features from ai-investment-intelligence-platform")
    
    # Check if we're in the right directory
    if not Path("ai-blog-assistant").exists():
        print("❌ Error: ai-blog-assistant directory not found")
        print("Please run this script from the directory containing both projects")
        sys.exit(1)
    
    if not Path("ai-investment-intelligence-platform").exists():
        print("❌ Error: ai-investment-intelligence-platform directory not found")
        print("Please ensure both projects are in the same directory")
        sys.exit(1)
    
    print_step(1, "Checking Project Structure")
    
    # Check key files exist
    files_to_check = [
        ("ai-blog-assistant/backend/app/models/finance.py", "Finance models"),
        ("ai-blog-assistant/backend/app/services/investment_data_collector.py", "Investment data collector"),
        ("ai-blog-assistant/backend/app/services/investment_analyzer.py", "Investment analyzer"),
        ("ai-blog-assistant/backend/app/services/investment_blog_generator.py", "Investment blog generator"),
        ("ai-blog-assistant/backend/app/api/investment.py", "Investment API endpoints"),
        ("ai-blog-assistant/backend/alembic/versions/003_add_investment_finance_tables.py", "Database migration"),
        ("ai-blog-assistant/frontend/src/components/InvestmentDashboard.jsx", "Frontend component")
    ]
    
    all_files_exist = True
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    if not all_files_exist:
        print("❌ Some required files are missing. Please ensure the integration was completed properly.")
        sys.exit(1)
    
    print_step(2, "Installing Python Dependencies")
    
    # Install backend dependencies
    os.chdir("ai-blog-assistant/backend")
    if not run_command("pip install -r requirements.txt", "Backend dependencies installation"):
        print("⚠️  Warning: Some dependencies may have failed to install")
    
    print_step(3, "Setting up Database")
    
    # Run database migrations
    if not run_command("alembic upgrade head", "Database migration"):
        print("❌ Database migration failed. Please check your database configuration.")
        os.chdir("../..")
        sys.exit(1)
    
    os.chdir("../..")
    
    print_step(4, "Updating Environment Configuration")
    update_env_file()
    
    print_step(5, "Installing Frontend Dependencies")
    
    # Install frontend dependencies
    os.chdir("ai-blog-assistant/frontend")
    if Path("package.json").exists():
        if not run_command("npm install", "Frontend dependencies installation"):
            print("⚠️  Warning: Frontend dependencies installation failed")
    else:
        print("⚠️  Warning: Frontend package.json not found")
    
    os.chdir("../..")
    
    print_step(6, "Integration Summary")
    
    print("\n🎉 Investment Intelligence Integration Complete!")
    print("\n📋 What was integrated:")
    print("   ✅ Finance and investment data models")
    print("   ✅ Market data collection services (Yahoo Finance, Alpha Vantage)")
    print("   ✅ Investment analysis and sentiment analysis")
    print("   ✅ AI-powered investment blog content generation")
    print("   ✅ RESTful API endpoints for investment features")
    print("   ✅ Database schema for investment data")
    print("   ✅ Frontend dashboard component")
    
    print("\n🔧 Next Steps:")
    print("   1. Update your .env file with API keys:")
    print("      - ALPHA_VANTAGE_API_KEY (free at https://www.alphavantage.co/)")
    print("      - OPENAI_API_KEY (from https://platform.openai.com/)")
    print("   2. Start the backend server: cd ai-blog-assistant/backend && uvicorn app.main:app --reload")
    print("   3. Start the frontend: cd ai-blog-assistant/frontend && npm start")
    print("   4. Access the investment dashboard at /investment-dashboard")
    
    print("\n📚 New API Endpoints Available:")
    print("   - POST /api/investment/profile - Create/update investment profile")
    print("   - GET /api/investment/profile - Get investment profile")
    print("   - POST /api/investment/watchlist/add/{symbol} - Add to watchlist")
    print("   - GET /api/investment/market-data/{symbol} - Get market data")
    print("   - GET /api/investment/analysis/{symbol} - Get stock analysis")
    print("   - POST /api/investment/generate-blog - Generate investment blog content")
    print("   - POST /api/investment/collect-data - Collect market and sentiment data")
    
    print("\n🎯 Features Available:")
    print("   - Investment profile management")
    print("   - Stock watchlist functionality")
    print("   - Real-time market data collection")
    print("   - Technical and sentiment analysis")
    print("   - AI-generated investment blog posts")
    print("   - Portfolio tracking and analysis")
    
    print("\n⚠️  Important Notes:")
    print("   - Alpha Vantage free tier has rate limits (5 API calls per minute)")
    print("   - OpenAI API usage will incur costs based on your usage")
    print("   - Market data is for informational purposes only")
    print("   - This is not financial advice - always do your own research")
    
    print("\n🔗 Documentation:")
    print("   - API docs available at: http://localhost:8000/docs")
    print("   - Investment models in: ai-blog-assistant/backend/app/models/finance.py")
    print("   - Services in: ai-blog-assistant/backend/app/services/investment_*")

if __name__ == "__main__":
    main()