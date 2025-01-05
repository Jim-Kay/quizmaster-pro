import os
import asyncio
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import UUID4

from ..flows.flow_wrapper import (
    FlowWrapper,
    FlowExecution,
    FlowExecutionCreate,
    FlowStatus
)
from ..dependencies import get_current_user
from ..database import get_db

# Set up logging
logger = logging.getLogger(__name__)

# Create router instance without prefix (prefix will be added in main.py)
router = APIRouter(tags=["flows"])

# This will be set by main.py
flow_wrapper: FlowWrapper = None

@router.post("/executions", response_model=FlowExecution, status_code=201)
async def create_flow_execution(
    flow_create: FlowExecutionCreate,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Create a new flow execution."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        # Check if flow exists
        try:
            flow_class = flow_wrapper.get_flow_class(flow_create.flow_name)
            if not flow_class:
                raise HTTPException(status_code=404, detail=f"Flow {flow_create.flow_name} not found")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Flow {flow_create.flow_name} not found")
        
        # Add user_id to initial state
        flow_create.initial_state = flow_create.initial_state or {}
        if "user_id" not in flow_create.initial_state:  # Only add if not already present
            flow_create.initial_state["user_id"] = str(current_user_id)
        logger.info(f"Creating flow execution with user ID: {flow_create.initial_state['user_id']}")
        
        return await flow_wrapper.create_execution(flow_create, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/start", response_model=FlowExecution)
async def start_flow_execution(
    execution_id: UUID4,
    background_tasks: BackgroundTasks,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Start a flow execution."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        # Get execution to verify it exists and belongs to user
        execution = await flow_wrapper.get_execution(execution_id, current_user_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
            
        # Add flow execution to background tasks
        background_tasks.add_task(flow_wrapper.start_execution, execution_id, current_user_id)
        
        # Return current execution status
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}", response_model=FlowExecution)
async def get_flow_execution(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Get flow execution status and details."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.get_execution(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions", response_model=List[FlowExecution])
async def list_flow_executions(
    status: Optional[FlowStatus] = None,
    flow_name: Optional[str] = None,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[FlowExecution]:
    """List flow executions with optional filtering."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.list_executions(status, flow_name, current_user_id)
    except Exception as e:
        logger.error(f"Error listing flow executions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}/logs")
async def get_flow_logs(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """Get flow execution logs."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        execution = await flow_wrapper.get_execution(execution_id, current_user_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
            
        if not execution.log_file or not os.path.exists(execution.log_file):
            return StreamingResponse(
                content=iter([f"No logs available. Status: {execution.status}, Error: {execution.error}\n"]),
                media_type="text/plain"
            )
            
        async def log_generator(exec_id: UUID4, log_file: str):
            with open(log_file, "r") as f:
                yield f.read()
                
            # If flow is still running, keep streaming logs
            current_exec = await flow_wrapper.get_execution(exec_id, current_user_id)
            if current_exec.status == FlowStatus.RUNNING:
                while True:
                    await asyncio.sleep(1)
                    with open(log_file, "r") as f:
                        f.seek(0, 2)  # Seek to end
                        if f.tell() > 0:  # If file has content
                            f.seek(0)  # Go back to start
                            yield f.read()  # Read entire file
                    
                    # Stop if flow is no longer running
                    current_exec = await flow_wrapper.get_execution(exec_id, current_user_id)
                    if current_exec.status != FlowStatus.RUNNING:
                        break
                        
        return StreamingResponse(
            content=log_generator(execution_id, execution.log_file),
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Error getting flow logs for {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/executions/{execution_id}")
async def delete_flow_execution(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a flow execution."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        await flow_wrapper.delete_execution(execution_id, current_user_id)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/stop")
async def stop_flow_execution(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Stop a running flow execution."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.stop_execution(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/pause")
async def pause_flow_execution(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Pause a running flow execution."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.pause_execution(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/resume")
async def resume_flow_execution(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Resume a paused flow execution."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.resume_execution(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming flow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}/metrics")
async def get_flow_execution_metrics(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get metrics for a flow execution."""
    try:
        if not flow_wrapper:
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.get_execution_metrics(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
