@echo off
REM AI Blog Assistant Setup Script for Windows

echo 🚀 Setting up AI Blog Assistant...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create environment file if it doesn't exist
if not exist .env (
    echo 📝 Creating environment file...
    copy .env.example .env
    echo ✅ Environment file created. Please edit .env with your configuration.
)

REM Create monitoring directories
echo 📁 Creating monitoring directories...
if not exist monitoring\folders mkdir monitoring\folders
if not exist monitoring\published mkdir monitoring\published
if not exist monitoring\failed mkdir monitoring\failed

REM Build and start services
echo 🐳 Building and starting Docker services...
docker-compose build
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend service is healthy
) else (
    echo ❌ Backend service is not responding
)

curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend service is healthy
) else (
    echo ❌ Frontend service is not responding
)

echo.
echo 🎉 Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your API keys and configuration
echo 2. Access the application:
echo    - Frontend: http://localhost:3000
echo    - Backend API: http://localhost:8000
echo    - API Documentation: http://localhost:8000/docs
echo 3. Check the monitoring folder: .\monitoring\folders
echo.
echo 🔧 Useful commands:
echo    - View logs: docker-compose logs -f
echo    - Stop services: docker-compose down
echo    - Restart services: docker-compose restart
echo    - Update services: docker-compose pull ^&^& docker-compose up -d
echo.
echo 📚 For more information, see README.md

pause