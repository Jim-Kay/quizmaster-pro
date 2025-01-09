from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
import uuid
import logging
from pydantic import BaseModel, UUID4
from datetime import datetime

from ..core.database import get_db
from ..core.models import Topic, Blueprint, TerminalObjective, EnablingObjective
from ..auth import get_current_user

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["blueprints"]
)

class EnablingObjectiveCreate(BaseModel):
    title: str
    description: str
    number: str
    cognitive_level: str

class TerminalObjectiveCreate(BaseModel):
    title: str
    description: str
    number: int
    cognitive_level: str
    enabling_objectives: List[EnablingObjectiveCreate]

class BlueprintCreate(BaseModel):
    title: str
    description: str
    terminal_objectives: List[TerminalObjectiveCreate]

class EnablingObjectiveResponse(BaseModel):
    enabling_objective_id: UUID4
    title: str
    description: str
    number: str
    cognitive_level: str
    created_at: datetime
    updated_at: datetime

class TerminalObjectiveResponse(BaseModel):
    terminal_objective_id: UUID4
    title: str
    description: str
    number: int
    cognitive_level: str
    created_at: datetime
    updated_at: datetime
    enabling_objectives: List[EnablingObjectiveResponse]

class BlueprintResponse(BaseModel):
    blueprint_id: UUID4
    title: str
    description: str | None
    topic_id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: datetime | None
    terminal_objectives_count: int
    enabling_objectives_count: int
    terminal_objectives: List[TerminalObjectiveResponse]

# Create new blueprint for a topic
@router.post("/{topic_id}/blueprints", response_model=dict, status_code=201)
async def create_blueprint(
    topic_id: UUID4,
    blueprint: BlueprintCreate,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # First verify the topic exists and belongs to the user
        topic_query = select(Topic).where(
            Topic.topic_id == topic_id,
            Topic.created_by == current_user_id
        )
        topic_result = await db.execute(topic_query)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Create the blueprint
        db_blueprint = Blueprint(
            blueprint_id=uuid.uuid4(),
            title=blueprint.title,
            description=blueprint.description,
            topic_id=topic_id,
            created_by=current_user_id
        )
        db.add(db_blueprint)

        # Create terminal objectives and their enabling objectives
        for term_obj in blueprint.terminal_objectives:
            db_terminal = TerminalObjective(
                terminal_objective_id=uuid.uuid4(),
                title=term_obj.title,
                description=term_obj.description,
                number=term_obj.number,
                cognitive_level=term_obj.cognitive_level,
                blueprint_id=db_blueprint.blueprint_id,
                topic_id=topic_id
            )
            db.add(db_terminal)

            # Create enabling objectives
            for en_obj in term_obj.enabling_objectives:
                db_enabling = EnablingObjective(
                    enabling_objective_id=uuid.uuid4(),
                    title=en_obj.title,
                    description=en_obj.description,
                    number=en_obj.number,
                    cognitive_level=en_obj.cognitive_level,
                    terminal_objective_id=db_terminal.terminal_objective_id
                )
                db.add(db_enabling)

        await db.commit()
        await db.refresh(db_blueprint)

        return {
            "message": "Blueprint created successfully",
            "id": str(db_blueprint.blueprint_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating blueprint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get all blueprints for a topic
@router.get("/{topic_id}/blueprints", response_model=List[BlueprintResponse])
async def get_blueprints(
    topic_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all blueprints for a topic."""
    try:
        # First verify the topic exists and belongs to the user
        topic_query = select(Topic).where(
            Topic.topic_id == topic_id,
            Topic.created_by == current_user_id
        )
        topic_result = await db.execute(topic_query)
        topic = topic_result.scalar_one_or_none()
        
        if not topic:
            raise HTTPException(
                status_code=404,
                detail="Topic not found or you don't have permission to access it"
            )

        # Get blueprints with objective counts
        query = (
            select(
                Blueprint,
                func.count(TerminalObjective.terminal_objective_id).label('terminal_count'),
                func.sum(
                    select(func.count(EnablingObjective.enabling_objective_id))
                    .where(EnablingObjective.terminal_objective_id == TerminalObjective.terminal_objective_id)
                    .scalar_subquery()
                ).label('enabling_count')
            )
            .outerjoin(TerminalObjective)
            .where(
                Blueprint.topic_id == topic_id,
                Blueprint.created_by == current_user_id
            )
            .group_by(Blueprint.blueprint_id)
        )
        
        result = await db.execute(query)
        blueprints = []
        
        for blueprint, terminal_count, enabling_count in result:
            # Get terminal objectives with their enabling objectives
            terminal_query = (
                select(TerminalObjective)
                .options(selectinload(TerminalObjective.enabling_objectives))
                .where(TerminalObjective.blueprint_id == blueprint.blueprint_id)
            )
            terminal_result = await db.execute(terminal_query)
            terminal_objectives = terminal_result.scalars().all()
            
            blueprints.append({
                **blueprint.__dict__,
                'terminal_objectives_count': terminal_count or 0,
                'enabling_objectives_count': enabling_count or 0,
                'terminal_objectives': terminal_objectives
            })
        
        return blueprints
    except Exception as e:
        logger.error(f"Error getting blueprints: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get a single blueprint by ID
@router.get("/{topic_id}/blueprints/{blueprint_id}", response_model=BlueprintResponse)
async def get_blueprint(
    topic_id: UUID4,
    blueprint_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # First verify the topic exists and belongs to the user
        topic_query = select(Topic).where(
            Topic.topic_id == topic_id,
            Topic.created_by == current_user_id
        )
        topic_result = await db.execute(topic_query)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Get the blueprint with objective counts and verify it belongs to the user
        query = (
            select(
                Blueprint,
                func.count(TerminalObjective.terminal_objective_id).label('terminal_count'),
                func.sum(
                    select(func.count(EnablingObjective.enabling_objective_id))
                    .where(EnablingObjective.terminal_objective_id == TerminalObjective.terminal_objective_id)
                    .scalar_subquery()
                ).label('enabling_count')
            )
            .outerjoin(TerminalObjective)
            .where(
                Blueprint.blueprint_id == blueprint_id,
                Blueprint.topic_id == topic_id,
                Blueprint.created_by == current_user_id
            )
            .group_by(Blueprint.blueprint_id)
        )
        
        result = await db.execute(query)
        row = result.first()

        if not row:
            logger.error(f"Blueprint not found: {blueprint_id}")
            raise HTTPException(status_code=404, detail="Blueprint not found")

        blueprint, terminal_count, enabling_count = row

        # Get terminal objectives with their enabling objectives
        terminal_query = (
            select(TerminalObjective)
            .options(selectinload(TerminalObjective.enabling_objectives))
            .where(TerminalObjective.blueprint_id == blueprint_id)
        )
        terminal_result = await db.execute(terminal_query)
        terminal_objectives = terminal_result.scalars().all()
        
        return {
            **blueprint.__dict__,
            'terminal_objectives_count': terminal_count or 0,
            'enabling_objectives_count': enabling_count or 0,
            'terminal_objectives': terminal_objectives
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blueprint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get blueprint count for a topic
@router.get("/{topic_id}/blueprints/count", response_model=dict)
async def get_blueprint_count(
    topic_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get blueprint count for a topic."""
    try:
        # First verify the topic exists and belongs to the user
        topic_query = select(Topic).where(
            Topic.topic_id == topic_id,
            Topic.created_by == current_user_id
        )
        topic_result = await db.execute(topic_query)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise HTTPException(
                status_code=404,
                detail="Topic not found or you don't have permission to access it"
            )

        # Get blueprint count
        query = select(func.count(Blueprint.blueprint_id)).where(
            Blueprint.topic_id == topic_id,
            Blueprint.created_by == current_user_id
        )
        
        result = await db.execute(query)
        count = result.scalar()

        return {"count": count}

    except Exception as e:
        logger.error(f"Error getting blueprint count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete a blueprint
@router.delete("/{topic_id}/blueprints/{blueprint_id}", status_code=204)
async def delete_blueprint(
    topic_id: UUID4,
    blueprint_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blueprint and all its associated objectives."""
    try:
        # Check if blueprint exists and belongs to the current user
        query = select(Blueprint).where(
            Blueprint.blueprint_id == blueprint_id,
            Blueprint.topic_id == topic_id,
            Blueprint.created_by == current_user_id
        )
        
        result = await db.execute(query)
        blueprint = result.scalar_one_or_none()
        
        if not blueprint:
            raise HTTPException(
                status_code=404,
                detail="Blueprint not found or you don't have permission to delete it"
            )
        
        await db.delete(blueprint)
        await db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting blueprint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
