"""Main FastAPI application module"""

from fastapi import FastAPI, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager

from .core.config import get_settings
from .core.database import init_db
from .auth import verify_token, get_current_user
from .core.models import User
from .routers import (
    topics,
    blueprint_generation,
    blueprints,
    user_settings,
    flow_execution
)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app"""
    # Startup: Initialize database models
    await init_db()
    yield
    # Cleanup (if needed)
    pass

app = FastAPI(
    title="QuizMaster Pro API backend",
    description="Backend API for QuizMaster Pro",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add token endpoint
@app.post("/api/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Token endpoint for testing"""
    return {"access_token": "test_token", "token_type": "bearer"}

# WebSocket endpoint
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint with token authentication"""
    try:
        # Verify token before accepting connection
        user = await verify_token(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        await websocket.send_json({"message": "Connection established"})
        
        try:
            while True:
                # Echo back received messages
                data = await websocket.receive_text()
                await websocket.send_text(data)
        except WebSocketDisconnect:
            await websocket.close()
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

# Include routers
app.include_router(topics.router, prefix="/api")
app.include_router(blueprint_generation.router, prefix="/api")
app.include_router(blueprints.router, prefix="/api")
app.include_router(user_settings.router, prefix="/api")
app.include_router(flow_execution.router, prefix="/api")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """Protected route for testing authentication"""
    return {"message": "You have access to the protected route", "user": current_user}
