"""Flow execution router"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from ..core.database import get_db
from ..core.models import FlowExecution, FlowLog, User
from ..auth import get_current_user
from .schemas import (
    FlowExecutionCreate,
    FlowExecutionResponse,
    FlowExecutionUpdate,
    FlowLogCreate,
    FlowLogResponse
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/flow-executions",
    tags=["flow-executions"]
)

@router.get("/", response_model=List[FlowExecutionResponse])
async def get_flow_executions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[FlowExecution]:
    """Get all flow executions for the current user"""
    result = await db.execute(
        select(FlowExecution)
        .filter(FlowExecution.user_id == current_user.user_id)
        .options(joinedload(FlowExecution.logs))
    )
    return result.scalars().all()

@router.post("/", response_model=FlowExecutionResponse, status_code=201)
async def create_flow_execution(
    flow_execution: FlowExecutionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Create a new flow execution"""
    db_flow_execution = FlowExecution(**flow_execution.model_dump(), user_id=current_user.user_id)
    db.add(db_flow_execution)
    try:
        await db.commit()
        await db.refresh(db_flow_execution)
        return db_flow_execution
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating flow execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{flow_execution_id}", response_model=FlowExecutionResponse)
async def get_flow_execution(
    flow_execution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Get a specific flow execution"""
    result = await db.execute(
        select(FlowExecution)
        .filter(FlowExecution.id == flow_execution_id, FlowExecution.user_id == current_user.user_id)
        .options(joinedload(FlowExecution.logs))
    )
    flow_execution = result.scalar_one_or_none()
    if not flow_execution:
        raise HTTPException(status_code=404, detail="Flow execution not found")
    return flow_execution

@router.put("/{flow_execution_id}", response_model=FlowExecutionResponse)
async def update_flow_execution(
    flow_execution_id: int,
    flow_execution_update: FlowExecutionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Update a flow execution"""
    result = await db.execute(
        select(FlowExecution)
        .filter(FlowExecution.id == flow_execution_id, FlowExecution.user_id == current_user.user_id)
    )
    flow_execution = result.scalar_one_or_none()
    if not flow_execution:
        raise HTTPException(status_code=404, detail="Flow execution not found")

    # Update fields
    update_data = flow_execution_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(flow_execution, field, value)

    try:
        await db.commit()
        await db.refresh(flow_execution)
        return flow_execution
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating flow execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{flow_execution_id}", status_code=204)
async def delete_flow_execution(
    flow_execution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a flow execution"""
    result = await db.execute(
        select(FlowExecution)
        .filter(FlowExecution.id == flow_execution_id, FlowExecution.user_id == current_user.user_id)
    )
    flow_execution = result.scalar_one_or_none()
    if not flow_execution:
        raise HTTPException(status_code=404, detail="Flow execution not found")

    try:
        await db.delete(flow_execution)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting flow execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{flow_execution_id}/logs", response_model=FlowLogResponse, status_code=201)
async def create_flow_log(
    flow_execution_id: int,
    flow_log: FlowLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowLog:
    """Create a new flow log entry"""
    # Verify flow execution exists and belongs to user
    result = await db.execute(
        select(FlowExecution)
        .filter(FlowExecution.id == flow_execution_id, FlowExecution.user_id == current_user.user_id)
    )
    flow_execution = result.scalar_one_or_none()
    if not flow_execution:
        raise HTTPException(status_code=404, detail="Flow execution not found")

    # Create log entry
    db_flow_log = FlowLog(**flow_log.model_dump(), flow_execution_id=flow_execution_id)
    db.add(db_flow_log)
    try:
        await db.commit()
        await db.refresh(db_flow_log)
        return db_flow_log
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating flow log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{flow_execution_id}/logs", response_model=List[FlowLogResponse])
async def get_flow_logs(
    flow_execution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[FlowLog]:
    """Get all logs for a flow execution"""
    # Verify flow execution exists and belongs to user
    result = await db.execute(
        select(FlowExecution)
        .filter(FlowExecution.id == flow_execution_id, FlowExecution.user_id == current_user.user_id)
    )
    flow_execution = result.scalar_one_or_none()
    if not flow_execution:
        raise HTTPException(status_code=404, detail="Flow execution not found")

    # Get logs
    result = await db.execute(
        select(FlowLog)
        .filter(FlowLog.flow_execution_id == flow_execution_id)
        .order_by(FlowLog.created_at)
    )
    return result.scalars().all()
