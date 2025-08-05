# AI Blog Assistant

A SaaS platform that helps content creators generate high-quality blog posts with SEO optimization and automated scheduling capabilities.

## Project Structure

```
ai-blog-assistant/
├── backend/                 # FastAPI backend application
│   ├── app/                # Application code
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend Docker configuration
├── frontend/               # React frontend application
│   ├── src/               # React source code
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile         # Frontend Docker configuration
├── database/              # Database configuration and migrations
│   ├── migrations/        # Alembic migration files
│   └── init.sql          # Initial database setup
├── docker-compose.yml     # Development environment orchestration
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Development Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your environment variables
3. Run the setup script: `python setup_full_system.py`
4. Start the development servers:
   - Windows: `start_dev.bat`
   - Unix/Mac: `./start_dev.sh`
5. Access the application at http://localhost:3000

## Technology Stack

- **Backend**: FastAPI, PostgreSQL, Redis, Celery
- **Frontend**: React, Tailwind CSS, React Query
- **Infrastructure**: Docker, Docker Compose
- **External APIs**: OpenAI GPT, WordPress, Medium

## Quick Start

1. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

2. **Run the setup script**
   ```bash
   python setup_full_system.py
   ```

3. **Start the application**
   ```bash
   # Windows
   start_dev.bat
   
   # Unix/Mac
   ./start_dev.sh
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs