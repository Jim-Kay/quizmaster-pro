from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from api.auth import get_current_user
from api.routers import topics, user_settings, blueprints, blueprint_generation

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QuizMaster Pro API backend",
    description="API for managing quiz topics and assessments",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    redirect_slashes=False
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to log all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {"detail": str(exc)}

# Include routers
app.include_router(
    topics.router,
    prefix="/api",
    tags=["topics"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    blueprints.router,
    prefix="/api/topics",
    tags=["blueprints"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    user_settings.router,
    prefix="/api",
    tags=["user_settings"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    blueprint_generation.router,
    prefix="/api",
    tags=["blueprint_generation"],
    dependencies=[Depends(get_current_user)]
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Welcome to QuizMaster Pro API"}
