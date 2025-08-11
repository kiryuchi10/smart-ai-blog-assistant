# AI Blog Assistant - Investment Automation MVP

A minimum viable product for automated investment blog generation with real-time financial data analysis and AI-powered content creation.

## 🚀 Features

- **Real-time Stock Analysis**: Fetch and analyze stock data using Yahoo Finance
- **AI-Powered Insights**: Generate investment analysis using OpenAI GPT
- **Automated Blog Generation**: Create professional investment blog posts
- **Technical Indicators**: RSI, moving averages, and trend analysis
- **Interactive Dashboard**: Web interface for managing analyses and blog posts
- **Data Visualization**: Stock performance charts and market sentiment

## 🛠 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Installation

1. **Clone and setup**:
   ```bash
   cd ai-blog-assistant
   python setup_mvp.py
   ```

2. **Configure API keys**:
   - Copy `backend/.env.example` to `backend/.env`
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

3. **Start the application**:
   - Windows: `start_mvp.bat`
   - Unix/Linux/Mac: `./start_mvp.sh`

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📊 Usage

### Stock Analysis
1. Enter stock tickers (e.g., "AAPL,GOOGL,MSFT")
2. Click "Analyze Stocks" to get real-time analysis
3. View technical indicators, recommendations, and AI insights

### Blog Generation
1. Select stocks to analyze
2. Choose a blog topic
3. Click "Generate Blog Post"
4. View generated content in the blog posts section

### API Endpoints

#### Stock Analysis
- `GET /api/v1/investment/stocks/{ticker}` - Analyze single stock
- `GET /api/v1/investment/stocks?tickers=AAPL,GOOGL` - Analyze multiple stocks

#### Blog Generation
- `POST /api/v1/investment/blog/generate` - Generate blog post
- `GET /api/v1/investment/blog/posts` - List blog posts
- `GET /api/v1/investment/blog/posts/{id}` - Get specific blog post

#### Market Overview
- `GET /api/v1/investment/market/overview` - Market sentiment analysis

## 🏗 Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── config.py        # Configuration settings
│   │   └── database.py      # Database setup
│   ├── models/
│   │   └── investment.py    # Database models
│   ├── services/
│   │   ├── yahoo_finance_service.py    # Data collection
│   │   ├── investment_analyzer.py      # AI analysis
│   │   └── blog_generator.py           # Content generation
│   └── api/
│       ├── investment.py    # Investment endpoints
│       └── health.py        # Health checks
├── requirements.txt
└── .env.example
```

### Frontend (React)
```
frontend/
├── src/
│   ├── components/
│   │   └── InvestmentDashboard.jsx    # Main dashboard
│   ├── App.js
│   └── App.css
└── package.json
```

## 🔧 Configuration

### Environment Variables
```env
# Database
DATABASE_URL=sqlite:///./investment_blog.db

# API Keys
OPENAI_API_KEY=your_openai_api_key_here

# Analysis Settings
DEFAULT_TICKERS=AAPL,GOOGL,MSFT,TSLA,NVDA
ANALYSIS_LOOKBACK_DAYS=30

# Blog Settings
DEFAULT_BLOG_TONE=professional
MAX_BLOG_LENGTH=2000
```

## 📈 Technical Indicators

The system calculates several technical indicators:

- **RSI (Relative Strength Index)**: Momentum oscillator (0-100)
- **Simple Moving Averages**: 5-day and 20-day SMAs
- **Price Change**: 30-day percentage change
- **Volume Analysis**: Average trading volume

## 🤖 AI Analysis

The AI analyzer provides:

- **Fundamental Analysis**: P/E ratios, market cap evaluation
- **Technical Analysis**: Trend identification, momentum analysis
- **Sentiment Analysis**: Market sentiment and recommendation
- **Risk Assessment**: Key risks and opportunities

## 📝 Blog Generation

Generated blog posts include:

- **Market Overview**: Current market conditions
- **Individual Stock Analysis**: Detailed analysis for each stock
- **Technical Insights**: Key technical indicators
- **Investment Recommendations**: Buy/sell/hold recommendations
- **Risk Disclaimers**: Professional disclaimers

## 🔍 Troubleshooting

### Common Issues

1. **Database errors**: Delete `investment_blog.db` and restart
2. **API key errors**: Ensure OpenAI API key is set in `.env`
3. **Port conflicts**: Change ports in configuration if needed
4. **Module not found**: Ensure virtual environment is activated

### Logs and Debugging

- Backend logs: Check console output when running uvicorn
- Frontend logs: Check browser developer console
- API testing: Use http://localhost:8000/docs for interactive testing

## 🚧 Development

### Adding New Features

1. **New Analysis Types**: Extend `InvestmentAnalyzer` class
2. **Additional Data Sources**: Create new service classes
3. **Enhanced Visualizations**: Add components to React frontend
4. **New Blog Templates**: Modify `BlogGenerator` class

### Database Schema

The MVP uses SQLite with three main tables:
- `stock_data`: Real-time stock information
- `market_analysis`: Analysis results and recommendations
- `blog_posts`: Generated blog content

## 📋 Roadmap

### Phase 1 (Current MVP)
- [x] Basic stock analysis
- [x] AI-powered blog generation
- [x] Simple web interface
- [x] Technical indicators

### Phase 2 (Future)
- [ ] Advanced charting
- [ ] Multiple data sources
- [ ] Automated publishing
- [ ] User authentication
- [ ] Portfolio tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This software is for educational and informational purposes only. It does not constitute financial advice. Always consult with qualified financial professionals before making investment decisions.