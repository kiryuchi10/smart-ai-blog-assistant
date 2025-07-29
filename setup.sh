#!/bin/bash

# AI Blog Assistant Development Setup Script

echo "🚀 Setting up AI Blog Assistant development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update the .env file with your actual API keys and configuration"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/app/models
mkdir -p backend/app/api
mkdir -p backend/app/services
mkdir -p backend/app/utils
mkdir -p backend/logs
mkdir -p uploads

# Set permissions
chmod +x setup.sh

# Build and start the development environment
echo "🐳 Building Docker containers..."
docker-compose build

echo "🔄 Starting development environment..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Display access information
echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "📊 Database and Redis:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "🛠️  Useful commands:"
echo "   Stop services: docker-compose down"
echo "   View logs: docker-compose logs -f [service_name]"
echo "   Restart services: docker-compose restart"
echo ""
echo "⚠️  Don't forget to:"
echo "   1. Update your .env file with real API keys"
echo "   2. Set up your OpenAI API key"
echo "   3. Configure external platform integrations"