"""Environment router."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..core.config import Settings, get_settings

class EnvironmentInfo(BaseModel):
    """Environment information model."""
    environment: str
    description: str
    color: str

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
    description="Returns information about the current environment including name, description, and color theme.",
    response_description="Environment details including name, description, and color"
)
async def get_environment(settings: Settings = Depends(get_settings)) -> EnvironmentResponse:
    """Get current environment information. This endpoint is public."""
    return EnvironmentResponse(
        data=EnvironmentInfo(
            environment=settings.environment_name,
            description=settings.environment_description,
            color=settings.environment_color
        ),
        meta={"timestamp": None}
    )
