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
3. Run `docker-compose up -d` to start the development environment
4. Access the application at http://localhost:3000

## Technology Stack

- **Backend**: FastAPI, PostgreSQL, Redis, Celery
- **Frontend**: React, Tailwind CSS, React Query
- **Infrastructure**: Docker, Docker Compose
- **External APIs**: OpenAI GPT, WordPress, Medium