import os
import asyncio
import logging
import hashlib
import json
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Header
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance without prefix (prefix will be added in main.py)
router = APIRouter(tags=["flows"])

# This will be set by main.py
flow_wrapper: FlowWrapper = None

# In-memory cache for idempotency keys
idempotency_cache: Dict[str, FlowExecution] = {}

@router.post("/executions", response_model=FlowExecution, status_code=201)
async def create_flow_execution(
    flow_create: FlowExecutionCreate,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: Optional[str] = Header(None)
) -> FlowExecution:
    """Create a new flow execution."""
    try:
        logger.info(f"Creating flow execution for flow: {flow_create.flow_name}")
        logger.info(f"Initial state: {flow_create.initial_state}")
        logger.info(f"Idempotency key: {x_idempotency_key}")
        
        # Check idempotency cache if key provided
        if x_idempotency_key and x_idempotency_key in idempotency_cache:
            logger.info(f"Found cached execution for idempotency key: {x_idempotency_key}")
            return idempotency_cache[x_idempotency_key]
        
        if not flow_wrapper:
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        # Check if flow exists
        try:
            logger.info(f"Getting flow class for: {flow_create.flow_name}")
            flow_class = flow_wrapper.get_flow_class(flow_create.flow_name)
            if not flow_class:
                logger.error(f"Flow {flow_create.flow_name} not found")
                raise HTTPException(status_code=404, detail=f"Flow {flow_create.flow_name} not found")
            logger.info(f"Found flow class: {flow_class.__name__}")
        except Exception as e:
            logger.error(f"Error getting flow class: {str(e)}", exc_info=True)
            raise HTTPException(status_code=404, detail=f"Flow {flow_create.flow_name} not found")
        
        # Add user_id to initial state
        flow_create.initial_state = flow_create.initial_state or {}
        if "user_id" not in flow_create.initial_state:  # Only add if not already present
            flow_create.initial_state["user_id"] = str(current_user_id)
        logger.info(f"Creating flow execution with user ID: {flow_create.initial_state['user_id']}")
        
        execution = await flow_wrapper.create_execution(flow_create, current_user_id)
        logger.info(f"Flow execution created with ID: {execution.id}")
        
        # Cache execution if idempotency key provided
        if x_idempotency_key:
            logger.info(f"Caching execution for idempotency key: {x_idempotency_key}")
            idempotency_cache[x_idempotency_key] = execution
            
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating flow execution: {str(e)}", exc_info=True)
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
        logger.info(f"Starting flow execution: {execution_id}")
        
        if not flow_wrapper:
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        # Get execution to verify it exists and belongs to user
        logger.info(f"Getting execution details for: {execution_id}")
        execution = await flow_wrapper.get_execution(execution_id, current_user_id)
        if not execution:
            logger.error(f"Flow execution not found: {execution_id}")
            raise HTTPException(status_code=404, detail="Flow execution not found")
            
        logger.info(f"Adding flow execution to background tasks: {execution_id}")
        # Add flow execution to background tasks
        background_tasks.add_task(flow_wrapper.start_execution, execution_id, current_user_id)
        
        # Return current execution status
        logger.info(f"Flow execution {execution_id} queued for start")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting flow execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}", response_model=FlowExecution)
async def get_flow_execution(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecution:
    """Get flow execution status and details."""
    try:
        logger.info(f"Getting flow execution status: {execution_id}")
        
        if not flow_wrapper:
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        execution = await flow_wrapper.get_execution(execution_id, current_user_id)
        logger.info(f"Flow execution {execution_id} status: {execution.status}")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow execution: {str(e)}", exc_info=True)
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
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.list_executions(status, flow_name, current_user_id)
    except Exception as e:
        logger.error(f"Error listing flow executions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}/logs")
async def get_flow_logs(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """Get flow execution logs."""
    try:
        logger.info(f"Getting logs for flow execution: {execution_id}")
        
        if not flow_wrapper:
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        execution = await flow_wrapper.get_execution(execution_id, current_user_id)
        if not execution:
            logger.error(f"Flow execution not found: {execution_id}")
            raise HTTPException(status_code=404, detail="Flow execution not found")
            
        if not execution.log_file or not os.path.exists(execution.log_file):
            logger.warning(f"No log file found for execution {execution_id}")
            return StreamingResponse(
                content=iter([f"No logs available. Status: {execution.status}, Error: {execution.error}\n"]),
                media_type="text/plain"
            )
            
        logger.info(f"Starting log stream for execution {execution_id}")
        
        async def log_generator():
            """Generate log content asynchronously."""
            try:
                # Send an initial empty chunk to establish the connection
                yield ""
                
                # Keep track of where we left off in the file
                last_position = 0
                
                while True:
                    try:
                        # Get current execution status
                        current_exec = await flow_wrapper.get_execution(execution_id, current_user_id)
                        if not current_exec:
                            logger.warning(f"Execution {execution_id} no longer exists")
                            break
                            
                        # Read any new content from the file
                        try:
                            with open(execution.log_file, "r", encoding='utf-8') as f:
                                f.seek(last_position)
                                new_content = f.read()
                                if new_content:
                                    logger.debug(f"New log content for {execution_id}: {len(new_content)} bytes")
                                    yield new_content
                                    last_position = f.tell()
                        except FileNotFoundError:
                            logger.debug(f"Log file not found yet for {execution_id}, waiting...")
                            # If file doesn't exist yet, wait and continue
                            await asyncio.sleep(0.1)
                            continue
                        
                        # If flow is done, send any remaining content and stop
                        if current_exec.status not in [FlowStatus.PENDING, FlowStatus.RUNNING]:
                            logger.info(f"Flow {execution_id} completed with status: {current_exec.status}")
                            break
                            
                        # Wait a bit before checking for more content
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Error reading logs for {execution_id}: {str(e)}", exc_info=True)
                        yield f"\nError reading logs: {str(e)}\n"
                        break
            except Exception as e:
                logger.error(f"Error in log generator for {execution_id}: {str(e)}", exc_info=True)
                yield f"\nError in log generator: {str(e)}\n"
                
        return StreamingResponse(
            content=log_generator(),
            media_type="text/plain",
            headers={
                'Content-Type': 'text/plain; charset=utf-8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Transfer-Encoding': 'chunked'
            }
        )
    except Exception as e:
        logger.error(f"Error getting flow logs for {execution_id}: {str(e)}", exc_info=True)
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
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        await flow_wrapper.delete_execution(execution_id, current_user_id)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flow execution: {str(e)}", exc_info=True)
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
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.stop_execution(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping flow execution: {str(e)}", exc_info=True)
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
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.pause_execution(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing flow execution: {str(e)}", exc_info=True)
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
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.resume_execution(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming flow execution: {str(e)}", exc_info=True)
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
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.get_execution_metrics(execution_id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
