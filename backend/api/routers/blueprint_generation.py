from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ..core.models import User, Topic, Blueprint, TerminalObjective, EnablingObjective
from ..auth import get_current_user
from ..core.database import get_db
from ..schemas.pydantic_schemas import BlueprintPydantic, BlueprintStatusResponse
from ..crews.blueprint_crew.blueprint_crew import BlueprintCrew

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["blueprint_generation"]
)

@router.post("/topics/{topic_id}/blueprints/generate", response_model=BlueprintPydantic)
async def generate_blueprint(
    topic_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """Generate a blueprint using AI for the specified topic."""
    try:
        # Check for existing blueprints in generating state
        stmt = select(Blueprint).where(
            and_(
                Blueprint.topic_id == topic_id,
                Blueprint.status == "generating"
            )
        )
        result = await db.execute(stmt)
        existing_blueprint = result.scalar_one_or_none()

        if existing_blueprint:
            # Check if generation has timed out
            if existing_blueprint.generation_started_at:
                time_elapsed = datetime.now(timezone.utc) - existing_blueprint.generation_started_at
                if time_elapsed.total_seconds() > 600:  # 10 minutes
                    existing_blueprint.status = "error"
                    existing_blueprint.description = "Blueprint generation timed out after 10 minutes"
                    await db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Previous blueprint generation timed out. Please try again."
                    )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A blueprint is already being generated for this topic"
            )

        # Get the topic
        topic = await db.get(Topic, topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )

        # Create a new blueprint
        blueprint = Blueprint(
            topic_id=topic_id,
            created_by=current_user_id,
            title=f"{topic.title} Blueprint",
            description="Generating blueprint...",
            status="generating",
            generation_started_at=datetime.now(timezone.utc)
        )
        db.add(blueprint)
        await db.commit()
        await db.refresh(blueprint)

        # Start background task
        background_tasks.add_task(
            generate_blueprint_background,
            blueprint.blueprint_id,
            topic.title,
            topic.description,
            current_user_id
        )

        return BlueprintPydantic(
            blueprint_id=blueprint.blueprint_id,
            title=blueprint.title,
            description=blueprint.description,
            topic_id=blueprint.topic_id,
            created_by=blueprint.created_by,
            terminal_objectives_count=blueprint.terminal_objectives_count or 0,
            enabling_objectives_count=blueprint.enabling_objectives_count or 0,
            status=blueprint.status
        )

    except Exception as e:
        logger.error(f"Error in generate_blueprint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/topics/{topic_id}/blueprints/{blueprint_id}/status", response_model=BlueprintStatusResponse)
async def get_blueprint_status(
    topic_id: UUID,
    blueprint_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the current status of a blueprint generation process."""
    try:
        # First verify that the topic exists
        topic = await db.get(Topic, topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )

        # Then get the blueprint, ensuring it belongs to the topic
        blueprint = await db.get(Blueprint, blueprint_id)
        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not found"
            )
            
        if blueprint.topic_id != topic_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not found for this topic"
            )

        # Check for timeout if status is generating
        if blueprint.status == "generating" and blueprint.generation_started_at:
            time_elapsed = datetime.now(timezone.utc) - blueprint.generation_started_at
            if time_elapsed.total_seconds() > 600:  # 10 minutes
                blueprint.status = "error"
                blueprint.description = "Blueprint generation timed out after 10 minutes"
                await db.commit()

        return BlueprintStatusResponse(
            id=blueprint.blueprint_id,
            status=blueprint.status,
            title=blueprint.title,
            description=blueprint.description,
            terminal_objectives_count=blueprint.terminal_objectives_count or 0,
            enabling_objectives_count=blueprint.enabling_objectives_count or 0,
        )

    except Exception as e:
        logger.error(f"Error in get_blueprint_status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def generate_blueprint_background(
    blueprint_id: UUID,
    topic_title: str,
    topic_description: str,
    current_user_id: UUID,
) -> None:
    """Background task to generate a blueprint using the BlueprintCrew."""
    import traceback
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from ..core.database import DATABASE_URL
    from ..core.models import Base, Blueprint, TerminalObjective, EnablingObjective

    # Create async engine and session
    async_engine = create_async_engine(str(DATABASE_URL))
    AsyncSessionLocal = async_sessionmaker(bind=async_engine)

    async def _generate_blueprint():
        try:
            logger.info(f"Starting background blueprint generation for topic {topic_title}")
            
            async with AsyncSessionLocal() as session:
                try:
                    # Update blueprint status to generating
                    result = await session.execute(
                        select(Blueprint).filter(Blueprint.blueprint_id == blueprint_id)
                    )
                    blueprint = result.scalar_one()
                    blueprint.status = "generating"
                    await session.commit()
                    
                    # Initialize inputs for blueprint crew
                    inputs = {
                        'topic': topic_title,
                        'description': topic_description,
                        'blueprint_id': blueprint_id,
                        'topic_id': None
                    }
                    logger.info("Initializing BlueprintCrew...")
                    blueprint_crew = BlueprintCrew(inputs=inputs)
                    
                    # Run the crew to generate blueprint
                    logger.info("Starting BlueprintCrew execution...")
                    blueprint_crew_result = blueprint_crew.run()
                    logger.info("BlueprintCrew execution completed")
                    logger.debug(f"BlueprintCrew result: {blueprint_crew_result}")

                    # Parse and save the result
                    result = await session.execute(
                        select(Blueprint).filter(Blueprint.blueprint_id == blueprint_id)
                    )
                    blueprint = result.scalar_one()
                    blueprint.status = "completed"
                    blueprint.title = blueprint_crew_result.title
                    blueprint.description = blueprint_crew_result.description
                    blueprint.terminal_objectives_count = len(blueprint_crew_result.terminal_objectives)
                    blueprint.enabling_objectives_count = sum(len(to.enabling_objectives) for to in blueprint_crew_result.terminal_objectives)
                    
                    # Save the terminal objectives
                    for to in blueprint_crew_result.terminal_objectives:
                        terminal_obj = TerminalObjective(
                            blueprint_id=blueprint_id,
                            title=to.title,
                            number=to.number,
                            description=to.description,
                            cognitive_level=to.cognitive_level,
                            topic_id=None,
                            enabling_objectives=[]
                        )
                        session.add(terminal_obj)
                        await session.flush()  # Get the ID
                        
                        # Save the enabling objectives
                        for eo in to.enabling_objectives:
                            enabling_obj = EnablingObjective(
                                terminal_objective_id=terminal_obj.terminal_objective_id,
                                title=eo.title,
                                number=eo.number,
                                description=eo.description,
                                cognitive_level=eo.cognitive_level
                            )
                            session.add(enabling_obj)
                    
                    await session.commit()
                    logger.info(f"Successfully saved blueprint {blueprint_id}")
                    
                except Exception as e:
                    error_trace = traceback.format_exc()
                    logger.error(f"Error in blueprint generation: {str(e)}")
                    logger.error(f"Traceback: {error_trace}")
                    try:
                        result = await session.execute(
                            select(Blueprint).filter(Blueprint.blueprint_id == blueprint_id)
                        )
                        blueprint = result.scalar_one()
                        blueprint.status = "error"
                        blueprint.description = f"Error generating blueprint: {str(e)}"
                        blueprint.error_details = error_trace
                        await session.commit()
                    except Exception as db_error:
                        logger.error(f"Failed to update blueprint error status: {str(db_error)}")
                    raise
                    
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Critical error in generate_blueprint_background: {str(e)}")
            logger.error(f"Traceback: {error_trace}")
            # Try one last time to update the blueprint status
            try:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(Blueprint).filter(Blueprint.blueprint_id == blueprint_id)
                    )
                    blueprint = result.scalar_one()
                    blueprint.status = "error"
                    blueprint.description = f"Critical error in blueprint generation: {str(e)}"
                    blueprint.error_details = error_trace
                    await session.commit()
            except Exception as final_e:
                logger.error(f"Failed to update blueprint status after error: {str(final_e)}")

    # Create event loop and run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_generate_blueprint())
    loop.close()
