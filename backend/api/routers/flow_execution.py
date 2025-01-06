import os
import asyncio
import logging
import hashlib
import json
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import UUID4
from fastapi import (
    APIRouter,
    WebSocket,
    HTTPException,
    Depends,
    BackgroundTasks,
    Header,
    Query,
)
from fastapi.responses import StreamingResponse
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, insert, func
from datetime import datetime, timedelta
from urllib.parse import unquote

from ..database import get_db
from ..auth import get_current_user, verify_token
from ..models import (
    FlowExecution as DBFlowExecution,
    IdempotencyKey,
    FlowExecutionStatus,
    FlowLog,
    LogLevel
)
from ..flows.flow_wrapper import (
    FlowWrapper,
    FlowExecutionCreate,
    FlowStatus,
    FlowExecution as FlowExecutionModel
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance without prefix (prefix will be added in main.py)
router = APIRouter(tags=["flows"])

# This will be set by main.py
flow_wrapper: FlowWrapper = None

@router.post("/executions", response_model=FlowExecutionModel, status_code=201)
async def create_flow_execution(
    flow_create: FlowExecutionCreate,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_idempotency_key: Optional[str] = Header(None)
) -> FlowExecutionModel:
    """Create a new flow execution."""
    try:
        logger.info(f"Creating flow execution for flow: {flow_create.flow_name}")
        logger.info(f"Initial state: {flow_create.initial_state}")
        logger.info(f"Idempotency key: {x_idempotency_key}")
        
        # Check idempotency key in database if provided
        if x_idempotency_key:
            stmt = select(IdempotencyKey).where(
                IdempotencyKey.key == x_idempotency_key,
                IdempotencyKey.user_id == current_user_id,
                IdempotencyKey.expires_at > func.now()  # Only consider non-expired keys
            )
            result = await db.execute(stmt)
            existing_key = result.scalar_one_or_none()
            
            if existing_key and existing_key.execution_id:
                logger.info(f"Found existing execution for idempotency key: {x_idempotency_key}")
                # Get the existing execution
                execution = await flow_wrapper.get_execution(existing_key.execution_id, current_user_id)
                if execution:
                    return execution
        
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
        
        # Store idempotency key in database if provided
        if x_idempotency_key:
            logger.info(f"Storing idempotency key in database: {x_idempotency_key}")
            idempotency_key = IdempotencyKey(
                key=x_idempotency_key,
                user_id=current_user_id,
                execution_id=execution.id,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=1)
            )
            db.add(idempotency_key)
            await db.commit()
            logger.info(f"Stored idempotency key: {x_idempotency_key} for execution: {execution.id}")
            
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating flow execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/start", response_model=FlowExecutionModel)
async def start_flow_execution(
    execution_id: UUID4,
    background_tasks: BackgroundTasks,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecutionModel:
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

@router.get("/executions/{execution_id}", response_model=FlowExecutionModel)
async def get_flow_execution(
    execution_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FlowExecutionModel:
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

@router.get("/executions", response_model=List[FlowExecutionModel])
async def list_flow_executions(
    status: Optional[FlowStatus] = None,
    flow_name: Optional[str] = None,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[FlowExecutionModel]:
    """List flow executions with optional filtering."""
    try:
        if not flow_wrapper:
            logger.error("Flow wrapper not initialized")
            raise HTTPException(status_code=500, detail="Flow wrapper not initialized")
            
        return await flow_wrapper.list_executions(status, flow_name, current_user_id)
    except Exception as e:
        logger.error(f"Error listing flow executions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def get_logs(db: AsyncSession, execution_id: str) -> List[Dict[str, Any]]:
    """Get all logs for a flow execution."""
    stmt = select(FlowLog).where(
        FlowLog.execution_id == execution_id
    ).order_by(FlowLog.timestamp)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [log.to_dict() for log in logs]

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

@router.websocket("/executions/{execution_id}/logs/ws")
async def websocket_logs(
    websocket: WebSocket,
    execution_id: UUID4,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for streaming flow execution logs."""
    try:
        # Accept connection first to allow proper error responses
        await websocket.accept()
        
        # Verify token and get user_id
        try:
            # First URL decode the token, then remove Bearer prefix
            decoded_token = unquote(token)
            decoded_token = decoded_token.replace("Bearer ", "").strip()
            user_id = await verify_token(decoded_token)
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            await websocket.send_json({"error": "Authentication failed"})
            await websocket.close(code=4001)
            return
            
        # Get execution and verify ownership
        execution = await flow_wrapper.get_execution(execution_id, user_id)
        if not execution:
            logger.error(f"Flow execution not found or unauthorized: {execution_id}")
            await websocket.send_json({"error": "Flow execution not found or unauthorized"})
            await websocket.close(code=4004)
            return
            
        # Log token details for debugging
        logger.debug(f"Raw token: {token}")
        logger.debug(f"Token length: {len(token) if token else 0}")
        
        # URL decode the token and remove Bearer prefix if present
        decoded_token = token.replace('Bearer ', '')
        logger.debug(f"Decoded token: {decoded_token}")
        logger.debug(f"Decoded token length: {len(decoded_token)}")
        
        # Verify token
        try:
            user_id = await verify_token(decoded_token)
            if not user_id:
                logger.warning(f"Token verification failed for execution {execution_id}")
                await websocket.send_text(json.dumps({
                    "error": "Invalid authentication token"
                }))
                await websocket.close(code=4001)
                return
                
            logger.info(f"WebSocket authenticated for user {user_id}, execution {execution_id}")
            
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            await websocket.send_text(json.dumps({
                "error": f"Authentication error: {str(e)}"
            }))
            await websocket.close(code=4001)
            return
            
        # First send existing logs
        try:
            logs = await get_logs(db, str(execution_id))
            if logs:
                for log in logs:
                    await websocket.send_json(log)
            else:
                await websocket.send_json({
                    "level": "INFO",
                    "message": "No logs available yet",
                    "timestamp": str(datetime.utcnow())
                })
        except Exception as e:
            logger.error(f"Error sending existing logs: {str(e)}", exc_info=True)
            await websocket.send_json({
                "level": "ERROR",
                "message": f"Failed to retrieve existing logs: {str(e)}",
                "timestamp": str(datetime.utcnow())
            })

        # Listen for new logs
        try:
            while True:
                msg = await websocket.receive_text()
                try:
                    msg = json.loads(msg)
                    if msg.get("type") == "log" and msg.get("payload"):
                        await websocket.send_json(msg["payload"])
                    else:
                        logger.warning(f"Missing required fields in notification: {msg}")
                        continue
                except Exception as e:
                    logger.error(f"Error processing notification: {str(e)}", exc_info=True)
                    continue
                    
        except WebSocketDisconnect as e:
            if e.code == 1000:
                logger.info(f"WebSocket connection closed normally for execution {execution_id}")
            else:
                logger.error(f"WebSocket error for execution {execution_id}: {str(e)}", exc_info=True)
                try:
                    await websocket.send_json({
                        "level": "ERROR",
                        "message": f"WebSocket error: {str(e)}",
                        "timestamp": str(datetime.utcnow())
                    })
                except:
                    pass
        finally:
            try:
                await websocket.close()
            except:
                pass
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=1011)
        except:
            pass

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
) -> FlowExecutionModel:
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
) -> FlowExecutionModel:
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
) -> FlowExecutionModel:
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
