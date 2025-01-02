from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from typing import List
import uuid
import logging
from pydantic import BaseModel, UUID4
from datetime import datetime

from ..database import get_db
from ..models import Topic, Blueprint
from ..auth import get_current_user
from .schemas import TopicBase, TopicCreate, TopicUpdate, TopicResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["topics"]
)

# Get all topics for current user
@router.get("/topics", response_model=List[TopicResponse])
async def get_topics(
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Topic).where(Topic.created_by == current_user_id)
    result = await db.execute(query)
    topics = result.scalars().all()
    return topics

# Create new topic
@router.post("/topics", response_model=TopicResponse, status_code=201)
async def create_topic(
    topic: TopicCreate,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        db_topic = Topic(
            topic_id=topic.topic_id or uuid.uuid4(),
            title=topic.title,
            description=topic.description,
            created_by=current_user_id
        )
        db.add(db_topic)
        await db.commit()
        await db.refresh(db_topic)
        return db_topic
    except Exception as e:
        logger.error(f"Error creating topic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get specific topic
@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Topic).where(
        Topic.topic_id == topic_id,
        Topic.created_by == current_user_id
    )
    result = await db.execute(query)
    topic = result.scalar_one_or_none()
    
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return topic

# Update topic
@router.put("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID4,
    topic_update: TopicUpdate,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if topic exists and belongs to user
    query = select(Topic).where(
        Topic.topic_id == topic_id,
        Topic.created_by == current_user_id
    )
    result = await db.execute(query)
    topic = result.scalar_one_or_none()
    
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Update topic
    update_stmt = (
        update(Topic)
        .where(Topic.topic_id == topic_id)
        .values(
            title=topic_update.title,
            description=topic_update.description,
            updated_at=datetime.now()
        )
        .returning(Topic)
    )
    result = await db.execute(update_stmt)
    updated_topic = result.scalar_one()
    await db.commit()
    
    return updated_topic

# Delete topic
@router.delete("/topics/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if topic exists and belongs to user
    query = select(Topic).where(
        Topic.topic_id == topic_id,
        Topic.created_by == current_user_id
    )
    result = await db.execute(query)
    topic = result.scalar_one_or_none()
    
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Delete topic
    delete_stmt = delete(Topic).where(Topic.topic_id == topic_id)
    await db.execute(delete_stmt)
    await db.commit()

# Get blueprint count for a topic
@router.get("/topics/{topic_id}/blueprints/count", response_model=dict)
async def get_blueprint_count(
    topic_id: UUID4,
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

        # Count blueprints for this topic
        count_query = select(func.count()).select_from(Blueprint).where(
            Blueprint.topic_id == topic_id
        )
        result = await db.execute(count_query)
        count = result.scalar()

        return {"count": count}
    except Exception as e:
        logger.error(f"Error counting blueprints: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
