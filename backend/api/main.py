"""Main FastAPI application module"""

from fastapi import FastAPI, Depends, status, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from .core.config import get_settings, Settings
from .core.database import init_db, get_db
from .auth import verify_token, get_current_user
from .core.models import User
from .routers import (
    topics,
    blueprint_generation,
    blueprints,
    user_settings,
    flow_execution,
    environment,
    dev
)

def create_app() -> FastAPI:
    """Create and configure a new FastAPI application instance."""
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager for FastAPI app"""
        # Startup: Initialize database models
        await init_db()
        yield
        # Cleanup (if needed)
        pass

    # Define OpenAPI tags metadata
    tags_metadata = [
        {
            "name": "Environment",
            "description": "Operations related to environment information and configuration",
        },
        {
            "name": "Health",
            "description": "Health check endpoint to verify API status",
        },
        {
            "name": "developer",
            "description": "Developer tools and testing endpoints",
        }
    ]

    app = FastAPI(
        title="QuizMaster Pro API backend",
        description="""
        Backend API for QuizMaster Pro - An intelligent quiz generation and management system.
        
        Key Features:
        * Environment Management
        * Topic Management
        * Blueprint Generation
        * Flow Execution
        """,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=tags_metadata
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure this properly in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]  # Added to expose headers for websocket
    )

    # Include routers
    app.include_router(environment.router, prefix="/api")
    app.include_router(topics.router, prefix="/api")
    app.include_router(blueprint_generation.router, prefix="/api")
    app.include_router(blueprints.router, prefix="/api")
    app.include_router(user_settings.router, prefix="/api")
    app.include_router(flow_execution.router, prefix="/api")
    app.include_router(dev.router)  # No prefix since it already has /dev prefix

    # Add token endpoint
    @app.post("/api/token")
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        """Token endpoint for testing"""
        return {"access_token": "test_token", "token_type": "bearer"}

    # WebSocket endpoint
    @app.websocket("/api/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        token: str,
        db: AsyncSession = Depends(get_db)
    ):
        """WebSocket endpoint with token authentication"""
        await websocket.accept()
        
        try:
            # Verify token and get user
            user = await verify_token(token, db)
            if user is None:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
                
            await websocket.send_json({
                "type": "connection_established",
                "user_id": str(user.user_id)
            })
            
            while True:
                try:
                    data = await websocket.receive_json()
                    await websocket.send_json({
                        "type": "message",
                        "data": data,
                        "user_id": str(user.user_id)
                    })
                except WebSocketDisconnect:
                    break
                    
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            
    return app

# Create default app instance
app = create_app()
