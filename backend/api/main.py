"""Main FastAPI application module"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.database import init_db
from .routers import (
    topics,
    blueprint_generation,
    blueprints,
    user_settings,
    flow_execution
)

settings = get_settings()

app = FastAPI(
    title="QuizMaster Pro API backend",
    description="Backend API for QuizMaster Pro",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics.router)
app.include_router(blueprint_generation.router)
app.include_router(blueprints.router)
app.include_router(user_settings.router)
app.include_router(flow_execution.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database models on startup"""
    await init_db()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
