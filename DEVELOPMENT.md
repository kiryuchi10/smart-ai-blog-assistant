# Development Guide

## Getting Started

### Prerequisites
- Docker Desktop
- Git
- Code editor (VS Code recommended)

### Quick Setup
1. Clone the repository
2. Run the setup script:
   - **Windows**: `setup.bat`
   - **Linux/Mac**: `./setup.sh`
3. Update `.env` file with your API keys
4. Access the application at http://localhost:3000

## Project Structure

```
ai-blog-assistant/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── tasks/          # Background tasks
│   │   └── utils/          # Utility functions
│   ├── migrations/         # Database migrations
│   └── tests/              # Backend tests
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   └── public/             # Static assets
└── database/               # Database configuration
```

## Development Workflow

### Backend Development
1. Make changes to Python files in `backend/app/`
2. The development server will auto-reload
3. Access API docs at http://localhost:8000/docs
4. Run tests: `docker-compose exec backend pytest`

### Frontend Development
1. Make changes to React files in `frontend/src/`
2. The development server will auto-reload
3. Access frontend at http://localhost:3000
4. Run tests: `docker-compose exec frontend npm test`

### Database Management
1. Create migration: `docker-compose exec backend alembic revision --autogenerate -m "description"`
2. Apply migrations: `docker-compose exec backend alembic upgrade head`
3. Access database: `docker-compose exec db psql -U postgres -d ai_blog_assistant`

## Environment Variables

Key environment variables to configure:

- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Application secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

## Docker Commands

- Start services: `docker-compose up -d`
- Stop services: `docker-compose down`
- View logs: `docker-compose logs -f [service]`
- Rebuild: `docker-compose build --no-cache`
- Shell access: `docker-compose exec [service] bash`

## Testing

### Backend Tests
```bash
docker-compose exec backend pytest
docker-compose exec backend pytest --cov=app
```

### Frontend Tests
```bash
docker-compose exec frontend npm test
docker-compose exec frontend npm run test:coverage
```

## Debugging

### Backend Debugging
- Check logs: `docker-compose logs -f backend`
- Access Python shell: `docker-compose exec backend python`
- Database queries: Check logs with `echo=True` in database config

### Frontend Debugging
- Check logs: `docker-compose logs -f frontend`
- Browser dev tools for client-side debugging
- React dev tools extension recommended

## Production Deployment

1. Update environment variables for production
2. Build production images: `docker-compose -f docker-compose.prod.yml build`
3. Deploy using your preferred orchestration tool (Kubernetes, Docker Swarm, etc.)

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Run the test suite
5. Submit a pull request