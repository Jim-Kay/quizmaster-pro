"""Environment router."""
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import os
from ..core.config import Settings, get_settings
from ..core.database import get_db

class EnvironmentInfo(BaseModel):
    """Environment information model."""
    environment: str
    description: str
    color: str
    database_name: str | None = None
    process_id: int

class EnvironmentResponse(BaseModel):
    """API response model for environment information."""
    data: EnvironmentInfo
    meta: dict

# Create a public router that doesn't require authentication
router = APIRouter(
    prefix="/environment",  # Main app will add /api prefix
    tags=["Environment"],  # Capitalized for better docs display
    include_in_schema=True,
    dependencies=[]  # No authentication dependency
)

@router.get(
    "",
    response_model=EnvironmentResponse,
    summary="Get Environment Information",
    description="Returns information about the current environment including name, description, color theme, database name, and process ID.",
    response_description="Environment details including name, description, color, database name, and process ID"
)
async def get_environment(
    response: Response,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db)
) -> EnvironmentResponse:
    """Get current environment information. This endpoint is public."""
    # Set cache control headers
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    
    # Clear settings cache to ensure we get fresh settings
    get_settings.cache_clear()
    settings = get_settings()
    
    # Query current database name using async connection
    try:
        # Use the async session to execute the query
        result = await db.execute(text("SELECT current_database() AS db_name"))
        row = await result.first()
        current_db = row.db_name if row else None
    except Exception as e:
        print(f"Error querying database: {e}")
        current_db = settings.postgres_db  # Fallback to settings
    
    return EnvironmentResponse(
        data=EnvironmentInfo(
            environment=settings.environment_name,
            description=settings.environment_description,
            color=settings.environment_color,
            database_name=current_db,
            process_id=os.getpid()
        ),
        meta={}
    )
