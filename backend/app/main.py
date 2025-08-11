"""
AI Blog Assistant - Investment Automation MVP
FastAPI backend for automated investment blog generation
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings
from app.core.database import init_db
from app.api.investment import router as investment_router
from app.api.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="AI Blog Assistant - Investment MVP",
    description="Automated investment blog generation with data visualization",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(investment_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "AI Blog Assistant - Investment Automation MVP"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )