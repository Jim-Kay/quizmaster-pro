import os
import hashlib
import json
import logging
import asyncio
from typing import Any, Dict, Optional, Type, List, get_args
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, UUID4

from crewai.flow.flow import Flow
from fastapi import HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import FlowExecution as DBFlowExecution, FlowExecutionStatus, FlowLog, LogLevel
from ..database import async_session_maker
from .db_logger import DatabaseLogger

# Set up logging
logger = logging.getLogger(__name__)

class FlowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class FlowExecution(BaseModel):
    id: UUID4
    flow_name: str
    status: FlowStatus
    state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    log_file: Optional[str] = None
    cache_key: Optional[str] = None

class FlowExecutionCreate(BaseModel):
    flow_name: str
    initial_state: Optional[Dict[str, Any]] = None
    use_cache: bool = True

class FlowWrapper:
    """
    A wrapper class for managing CrewAI flow executions.
    Handles flow instantiation, execution tracking, and state management.
    """
    
    def __init__(self, enable_caching: bool = True):
        """Initialize the flow wrapper."""
        self._flows: Dict[str, Type[Flow]] = {}
        self._project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self._cache_dir = os.path.join(self._project_root, "cache", "flows")
        self._enable_caching = enable_caching
        self._cache: Dict[str, Any] = {}
        
        if enable_caching:
            os.makedirs(self._cache_dir, exist_ok=True)
    
    def _generate_cache_key(self, flow_name: str, initial_state: Dict[str, Any]) -> str:
        """Generate a cache key based on flow name and initial state."""
        sorted_state = dict(sorted(initial_state.items())) if initial_state else {}
        state_str = json.dumps(sorted_state, sort_keys=True)
        hash_input = f"{flow_name}:{state_str}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get the cache file path for a given cache key."""
        return os.path.join(self._cache_dir, f"{cache_key}.json")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load cached flow results if they exist."""
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load cache: {str(e)}")
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save flow results to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save to cache: {str(e)}")
    
    def register_flow(self, name: str, flow_class: Type[Flow]) -> None:
        """Register a flow class with a given name."""
        self._flows[name] = flow_class
    
    def get_flow_class(self, name: str) -> Type[Flow]:
        """Get a flow class by name."""
        if name not in self._flows:
            raise HTTPException(status_code=404, detail=f"Flow '{name}' not found")
        return self._flows[name]
    
    async def get_execution(self, execution_id: UUID4, user_id: UUID4) -> FlowExecution:
        """Get flow execution status and details."""
        async with async_session_maker() as session:
            stmt = select(DBFlowExecution).where(
                DBFlowExecution.id == execution_id,
                DBFlowExecution.user_id == user_id
            )
            result = await session.execute(stmt)
            db_execution = result.scalar_one_or_none()
            
            if not db_execution:
                raise HTTPException(status_code=404, detail="Flow execution not found")
            
            return FlowExecution(
                id=db_execution.id,
                flow_name=db_execution.flow_name,
                status=db_execution.status.value,
                state=db_execution.state,
                error=db_execution.error,
                created_at=db_execution.created_at,
                started_at=db_execution.started_at,
                completed_at=db_execution.completed_at,
                log_file=db_execution.log_file,
                cache_key=db_execution.cache_key
            )
    
    async def create_execution(self, flow_create: FlowExecutionCreate, user_id: UUID4) -> FlowExecution:
        """Create a new flow execution."""
        flow_class = self.get_flow_class(flow_create.flow_name)
        
        cache_key = None
        if self._enable_caching and flow_create.use_cache:
            cache_key = self._generate_cache_key(flow_create.flow_name, flow_create.initial_state or {})
            if cache_key and (cached_data := self._load_from_cache(cache_key)):
                logger.info(f"Found cached result for key: {cache_key}")
                db_execution = DBFlowExecution(
                    id=uuid4(),
                    flow_name=flow_create.flow_name,
                    status=FlowExecutionStatus.COMPLETED,
                    state=cached_data.get("state_dict"),
                    created_at=datetime.utcnow(),
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    cache_key=cache_key,
                    user_id=user_id
                )
            else:
                db_execution = DBFlowExecution(
                    id=uuid4(),
                    flow_name=flow_create.flow_name,
                    status=FlowExecutionStatus.PENDING,
                    state=flow_create.initial_state,
                    cache_key=cache_key,
                    user_id=user_id
                )
        else:
            db_execution = DBFlowExecution(
                id=uuid4(),
                flow_name=flow_create.flow_name,
                status=FlowExecutionStatus.PENDING,
                state=flow_create.initial_state,
                user_id=user_id
            )
        
        async with async_session_maker() as session:
            session.add(db_execution)
            await session.commit()
            await session.refresh(db_execution)
        
        return FlowExecution(
            id=db_execution.id,
            flow_name=db_execution.flow_name,
            status=db_execution.status.value,
            state=db_execution.state,
            error=db_execution.error,
            created_at=db_execution.created_at,
            started_at=db_execution.started_at,
            completed_at=db_execution.completed_at,
            log_file=db_execution.log_file,
            cache_key=db_execution.cache_key
        )
    
    async def start_execution(self, execution_id: UUID4, user_id: UUID4) -> FlowExecution:
        """Start a flow execution."""
        async with async_session_maker() as session:
            stmt = select(DBFlowExecution).where(
                DBFlowExecution.id == execution_id,
                DBFlowExecution.user_id == user_id
            )
            result = await session.execute(stmt)
            db_execution = result.scalar_one_or_none()
            
            if not db_execution:
                raise HTTPException(status_code=404, detail="Flow execution not found")
            
            if db_execution.status != FlowExecutionStatus.PENDING:
                raise HTTPException(status_code=400, detail="Flow execution is not in pending state")
            
            # Get flow class and create instance
            flow_class = self.get_flow_class(db_execution.flow_name)
            
            # Get the state type from the Flow's _initial_state_T
            state_type = getattr(flow_class, "_initial_state_T", None)
            if state_type is None:
                # Fallback to looking at the Flow's base class
                for base in flow_class.__bases__:
                    if hasattr(base, "__origin__") and base.__origin__ is Flow:
                        state_type = get_args(base)[0]
                        break
                else:
                    raise ValueError("Could not determine state type for flow")
            
            # Convert execution state to proper state type
            state_dict = db_execution.state.copy() if db_execution.state else {}
            state = state_type(**state_dict)
            
            # Create flow instance with initial state
            flow = flow_class(state=state)
            
            # Update execution in database
            db_execution.status = FlowExecutionStatus.RUNNING
            db_execution.started_at = datetime.utcnow()
            await session.commit()
            await session.refresh(db_execution)
            
            # Set up database logger
            db_logger = DatabaseLogger(f"flow_{execution_id}", execution_id)
            await db_logger.start_worker()
            
            # Start flow execution asynchronously
            try:
                # Run flow in a separate thread to avoid asyncio issues
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(flow.kickoff)
                    result = future.result()  # Wait for completion
                    
                    # Save results to cache if enabled
                    if self._enable_caching and db_execution.cache_key:
                        cache_data = {
                            'raw_output': str(result),
                            'raw_state': str(flow.state),
                            'state_dict': flow.state.dict() if hasattr(flow.state, 'dict') else None,
                            'created_at': datetime.utcnow().isoformat()
                        }
                        self._save_to_cache(db_execution.cache_key, cache_data)
                    
                    # Update execution with final state and status
                    db_execution.state = flow.state.dict()
                    db_execution.status = FlowExecutionStatus.COMPLETED
                    db_execution.completed_at = datetime.utcnow()
                    await session.commit()
                    await session.refresh(db_execution)
                    await db_logger.ainfo("Flow execution completed successfully", {
                        "state": db_execution.state
                    })
            except Exception as e:
                await db_logger.aerror(f"Flow execution failed: {str(e)}")
                db_execution.status = FlowExecutionStatus.FAILED
                db_execution.error = str(e)
                db_execution.completed_at = datetime.utcnow()
                await session.commit()
                await session.refresh(db_execution)
                
                # Cache error state if enabled
                if self._enable_caching and db_execution.cache_key:
                    error_data = {
                        'error': str(e),
                        'raw_state': str(flow.state) if flow else None,
                        'created_at': datetime.utcnow().isoformat()
                    }
                    self._save_to_cache(db_execution.cache_key, error_data)
                raise
            finally:
                await db_logger.stop_worker()
            
            # Convert to Pydantic model and return
            return FlowExecution(
                id=db_execution.id,
                flow_name=db_execution.flow_name,
                status=db_execution.status.value,
                state=db_execution.state,
                error=db_execution.error,
                created_at=db_execution.created_at,
                started_at=db_execution.started_at,
                completed_at=db_execution.completed_at,
                log_file=db_execution.log_file,
                cache_key=db_execution.cache_key
            )
    
    async def list_executions(self, 
                            status: Optional[FlowStatus] = None,
                            flow_name: Optional[str] = None,
                            user_id: Optional[UUID4] = None) -> list[FlowExecution]:
        """List flow executions with optional filtering."""
        async with async_session_maker() as session:
            stmt = select(DBFlowExecution)
            if status:
                stmt = stmt.where(DBFlowExecution.status == status)
            if flow_name:
                stmt = stmt.where(DBFlowExecution.flow_name == flow_name)
            if user_id:
                stmt = stmt.where(DBFlowExecution.user_id == user_id)
            result = await session.execute(stmt)
            db_executions = result.scalars().all()
        
        executions = []
        for db_execution in db_executions:
            execution = FlowExecution(
                id=db_execution.id,
                flow_name=db_execution.flow_name,
                status=db_execution.status.value,
                state=db_execution.state,
                error=db_execution.error,
                created_at=db_execution.created_at,
                started_at=db_execution.started_at,
                completed_at=db_execution.completed_at,
                log_file=db_execution.log_file,
                cache_key=db_execution.cache_key
            )
            executions.append(execution)
        
        return executions
    
    async def delete_execution(self, execution_id: UUID4, user_id: UUID4) -> None:
        """Delete a flow execution."""
        async with async_session_maker() as session:
            stmt = select(DBFlowExecution).where(
                DBFlowExecution.id == execution_id,
                DBFlowExecution.user_id == user_id
            )
            result = await session.execute(stmt)
            db_execution = result.scalar_one_or_none()
            if db_execution:
                await session.delete(db_execution)
                await session.commit()
            
    async def stop_execution(self, execution_id: UUID4, user_id: UUID4) -> FlowExecution:
        """Stop a running flow execution."""
        execution = await self.get_execution(execution_id, user_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
            
        if execution.status != FlowStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Flow execution is not running")
            
        execution.status = FlowStatus.FAILED
        execution.error = "Flow execution stopped by user"
        execution.completed_at = datetime.utcnow()
        async with async_session_maker() as session:
            session.merge(execution)
            await session.commit()
        return execution
        
    async def pause_execution(self, execution_id: UUID4, user_id: UUID4) -> FlowExecution:
        """Pause a running flow execution."""
        execution = await self.get_execution(execution_id, user_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
            
        if execution.status != FlowStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Flow execution is not running")
            
        execution.status = FlowStatus.PAUSED
        async with async_session_maker() as session:
            session.merge(execution)
            await session.commit()
        return execution
        
    async def resume_execution(self, execution_id: UUID4, user_id: UUID4) -> FlowExecution:
        """Resume a paused flow execution."""
        execution = await self.get_execution(execution_id, user_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
            
        if execution.status != FlowStatus.PAUSED:
            raise HTTPException(status_code=400, detail="Flow execution is not paused")
            
        execution.status = FlowStatus.RUNNING
        async with async_session_maker() as session:
            session.merge(execution)
            await session.commit()
        return execution
        
    async def get_execution_metrics(self, execution_id: UUID4, user_id: UUID4) -> Dict[str, Any]:
        """Get metrics for a flow execution."""
        execution = await self.get_execution(execution_id, user_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Flow execution not found")
            
        # Calculate duration
        duration = None
        if execution.completed_at and execution.created_at:
            duration = (execution.completed_at - execution.created_at).total_seconds()
            
        return {
            "status": execution.status,
            "created_at": execution.created_at,
            "completed_at": execution.completed_at,
            "duration_seconds": duration,
            "error": execution.error,
            "cache_hit": bool(execution.cache_key and os.path.exists(self._get_cache_path(execution.cache_key)))
        }
