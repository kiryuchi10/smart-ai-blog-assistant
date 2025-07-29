@echo off
echo 🚀 Setting up AI Blog Assistant development environment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please update the .env file with your actual API keys and configuration
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist backend\app\models mkdir backend\app\models
if not exist backend\app\api mkdir backend\app\api
if not exist backend\app\services mkdir backend\app\services
if not exist backend\app\utils mkdir backend\app\utils
if not exist backend\logs mkdir backend\logs
if not exist uploads mkdir uploads

REM Build and start the development environment
echo 🐳 Building Docker containers...
docker-compose build

echo 🔄 Starting development environment...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo 🔍 Checking service status...
docker-compose ps

REM Display access information
echo.
echo ✅ Setup complete!
echo.
echo 🌐 Access your application:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000
echo    API Documentation: http://localhost:8000/docs
echo.
echo 📊 Database and Redis:
echo    PostgreSQL: localhost:5432
echo    Redis: localhost:6379
echo.
echo 🛠️  Useful commands:
echo    Stop services: docker-compose down
echo    View logs: docker-compose logs -f [service_name]
echo    Restart services: docker-compose restart
echo.
echo ⚠️  Don't forget to:
echo    1. Update your .env file with real API keys
echo    2. Set up your OpenAI API key
echo    3. Configure external platform integrations
echo.
pause