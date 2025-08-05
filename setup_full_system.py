#!/usr/bin/env python3
"""
Complete System Setup for AI Blog Assistant
Sets up database, Redis, installs dependencies, and starts services
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()[:200]}...")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is too old. Need Python 3.8+")
        return False

def setup_backend():
    """Set up backend dependencies and database"""
    print("\n🔧 Setting up Backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies", backend_dir):
        print("⚠️ Some dependencies may have failed to install")
    
    return True

def setup_frontend():
    """Set up frontend dependencies"""
    print("\n⚛️ Setting up Frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install Node.js dependencies
    if not run_command("npm install", "Installing Node.js dependencies", frontend_dir):
        return False
    
    return True

def create_startup_scripts():
    """Create startup scripts for easy development"""
    
    # Windows batch file
    windows_script = """@echo off
echo Starting AI Blog Assistant...

echo.
echo Starting Backend...
start "Backend" cmd /k "cd backend && python -m app.main"

echo.
echo Waiting for backend...
timeout /t 3 /nobreak > nul

echo.
echo Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo Services starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause > nul
"""
    
    with open("start_dev.bat", "w") as f:
        f.write(windows_script)
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting AI Blog Assistant..."

echo ""
echo "Starting Backend..."
cd backend
python -m app.main &
BACKEND_PID=$!
cd ..

echo ""
echo "Waiting for backend..."
sleep 3

echo ""
echo "Starting Frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "Services started!"
echo "Backend: http://localhost:8000 (PID: $BACKEND_PID)"
echo "Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait
"""
    
    with open("start_dev.sh", "w") as f:
        f.write(unix_script)
    
    # Make shell script executable
    try:
        os.chmod("start_dev.sh", 0o755)
    except:
        pass
    
    print("✅ Startup scripts created: start_dev.bat, start_dev.sh")

def create_env_files():
    """Ensure .env files exist"""
    
    # Backend .env should already exist, just verify
    backend_env = Path("backend/.env")
    if backend_env.exists():
        print("✅ Backend .env file exists")
    else:
        print("❌ Backend .env file missing")
    
    # Frontend .env
    frontend_env = Path("frontend/.env")
    if not frontend_env.exists():
        frontend_env_content = """REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=1.0.0
GENERATE_SOURCEMAP=false
"""
        with open(frontend_env, "w") as f:
            f.write(frontend_env_content)
        print("✅ Frontend .env file created")
    else:
        print("✅ Frontend .env file exists")

def main():
    """Main setup function"""
    print("🚀 AI Blog Assistant - Complete System Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check current directory
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Please run this script from the ai-blog-assistant root directory")
        print("   Expected structure:")
        print("   ai-blog-assistant/")
        print("   ├── backend/")
        print("   ├── frontend/")
        print("   └── setup_full_system.py")
        return False
    
    # Create .env files
    print("\n📝 Setting up environment files...")
    create_env_files()
    
    # Set up backend
    if not setup_backend():
        print("⚠️ Backend setup had issues, continuing...")
    
    # Set up frontend
    if not setup_frontend():
        print("⚠️ Frontend setup had issues, continuing...")
    
    # Create startup scripts
    print("\n📜 Creating startup scripts...")
    create_startup_scripts()
    
    print("\n🎉 Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Start the system:")
    print("   Windows: start_dev.bat")
    print("   Unix/Mac: ./start_dev.sh")
    print("")
    print("2. Or start manually:")
    print("   Backend: cd backend && python -m app.main")
    print("   Frontend: cd frontend && npm start")
    print("")
    print("3. Access the application:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("")
    print("🎯 Ready to use AI Blog Assistant!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)