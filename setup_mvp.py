#!/usr/bin/env python3
"""
Setup script for AI Blog Assistant Investment MVP
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False

def setup_backend():
    """Setup backend environment and dependencies"""
    print("\n🔧 Setting up backend...")
    
    backend_dir = Path("backend")
    
    # Create virtual environment
    if not run_command("python -m venv venv", cwd=backend_dir):
        return False
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    if not run_command(f"{pip_cmd} install --upgrade pip", cwd=backend_dir):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", cwd=backend_dir):
        return False
    
    # Create .env file if it doesn't exist
    env_file = backend_dir / ".env"
    env_example = backend_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✓ Created .env file from .env.example")
    
    # Initialize database
    if not run_command(f"{python_cmd} -c \"from app.core.database import init_db; import asyncio; asyncio.run(init_db())\"", cwd=backend_dir):
        print("⚠ Database initialization failed, but continuing...")
    
    return True

def setup_frontend():
    """Setup frontend environment and dependencies"""
    print("\n🎨 Setting up frontend...")
    
    frontend_dir = Path("frontend")
    
    # Check if package.json exists, create if not
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        package_content = {
            "name": "ai-blog-assistant-frontend",
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": [
                    "react-app",
                    "react-app/jest"
                ]
            },
            "browserslist": {
                "production": [
                    ">0.2%",
                    "not dead",
                    "not op_mini all"
                ],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version"
                ]
            }
        }
        
        import json
        with open(package_json, 'w') as f:
            json.dump(package_content, f, indent=2)
        print("✓ Created package.json")
    
    # Install dependencies
    if not run_command("npm install", cwd=frontend_dir):
        return False
    
    return True

def create_start_scripts():
    """Create convenient start scripts"""
    print("\n📝 Creating start scripts...")
    
    # Windows batch file
    with open("start_mvp.bat", "w") as f:
        f.write("""@echo off
echo Starting AI Blog Assistant Investment MVP...

echo Starting backend...
start "Backend" cmd /k "cd backend && venv\\Scripts\\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo Starting frontend...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
pause
""")
    
    # Unix shell script
    with open("start_mvp.sh", "w") as f:
        f.write("""#!/bin/bash
echo "Starting AI Blog Assistant Investment MVP..."

echo "Starting backend..."
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 3

echo "Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for Ctrl+C
trap 'kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait
""")
    
    # Make shell script executable
    if os.name != 'nt':
        os.chmod("start_mvp.sh", 0o755)
    
    print("✓ Created start scripts")

def main():
    """Main setup function"""
    print("🚀 AI Blog Assistant Investment MVP Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed")
        return False
    
    # Setup frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        return False
    
    # Create start scripts
    create_start_scripts()
    
    print("\n✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Add your OpenAI API key to backend/.env")
    print("2. Run start_mvp.bat (Windows) or ./start_mvp.sh (Unix/Linux/Mac)")
    print("3. Open http://localhost:3000 to use the application")
    print("4. API documentation available at http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)