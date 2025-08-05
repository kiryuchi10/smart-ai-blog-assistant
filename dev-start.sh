#!/bin/bash

# Development startup script

set -e

echo "🔧 Starting AI Blog Assistant in development mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run setup.sh first."
    exit 1
fi

# Start development services
echo "🐳 Starting development services..."
docker-compose -f docker-compose.yml up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Start backend in development mode
echo "🚀 Starting backend in development mode..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend in development mode
echo "🎨 Starting frontend in development mode..."
cd frontend
npm install
npm start &
FRONTEND_PID=$!
cd ..

# Start Celery worker
echo "⚙️ Starting Celery worker..."
cd backend
celery -A app.worker worker --loglevel=info &
WORKER_PID=$!
cd ..

echo ""
echo "✅ Development environment started!"
echo ""
echo "📋 Services:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Database: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "🛑 To stop all services, press Ctrl+C"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping development services..."
    kill $BACKEND_PID $FRONTEND_PID $WORKER_PID 2>/dev/null || true
    docker-compose down
    echo "✅ All services stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Wait for user to stop
wait