"""Topics router"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from ..core.database import get_db
from ..core.models import Topic, Blueprint, User
from ..auth import get_current_user
from .schemas import TopicBase, TopicCreate, TopicUpdate, TopicResponse

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/topics",
    tags=["topics"]
)

@router.get("/", response_model=List[TopicResponse])
async def get_topics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Topic]:
    """Get all topics for the current user"""
    result = await db.execute(
        select(Topic)
        .filter(Topic.user_id == current_user.user_id)
        .options(joinedload(Topic.blueprints))
    )
    return result.scalars().all()

@router.post("/", response_model=TopicResponse, status_code=201)
async def create_topic(
    topic: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Topic:
    """Create a new topic"""
    db_topic = Topic(**topic.model_dump(), user_id=current_user.user_id)
    db.add(db_topic)
    try:
        await db.commit()
        await db.refresh(db_topic)
        return db_topic
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Topic:
    """Get a specific topic"""
    result = await db.execute(
        select(Topic)
        .filter(Topic.id == topic_id, Topic.user_id == current_user.user_id)
        .options(joinedload(Topic.blueprints))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    topic_update: TopicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Topic:
    """Update a topic"""
    result = await db.execute(
        select(Topic)
        .filter(Topic.id == topic_id, Topic.user_id == current_user.user_id)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Update fields
    update_data = topic_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(topic, field, value)

    try:
        await db.commit()
        await db.refresh(topic)
        return topic
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a topic"""
    result = await db.execute(
        select(Topic)
        .filter(Topic.id == topic_id, Topic.user_id == current_user.user_id)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    try:
        await db.delete(topic)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{topic_id}/blueprints/count", response_model=dict)
async def get_blueprint_count(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get the count of blueprints for a topic"""
    result = await db.execute(
        select(Topic)
        .filter(Topic.id == topic_id, Topic.user_id == current_user.user_id)
        .options(joinedload(Topic.blueprints))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return {"count": len(topic.blueprints)}
