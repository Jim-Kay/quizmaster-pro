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

from api.core.models import FlowExecution as DBFlowExecution, FlowExecutionStatus, FlowLog, LogLevel
from api.core.database import async_session_maker
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
    
    async def start_execution(self, execution_id: UUID4, user_id: UUID4) -> None:
        """Start a flow execution."""
        logger.info(f"Starting flow execution: {execution_id}")
        
        try:
            async with async_session_maker() as session:
                # Get execution
                stmt = select(DBFlowExecution).where(
                    DBFlowExecution.id == execution_id,
                    DBFlowExecution.user_id == user_id
                )
                result = await session.execute(stmt)
                execution = result.scalar_one_or_none()
                
                if not execution:
                    raise HTTPException(status_code=404, detail="Flow execution not found")
                    
                # Check if execution is in correct state
                if execution.status != FlowExecutionStatus.PENDING:
                    logger.error(f"Flow execution {execution_id} is not in pending state: {execution.status}")
                    # If we have a cached result, update the execution state
                    if execution.cache_key:
                        cached_result = self._load_from_cache(execution.cache_key)
                        if cached_result:
                            logger.info(f"Using cached result for execution {execution_id}")
                            execution.state = cached_result.get('state')
                            execution.status = FlowExecutionStatus.COMPLETED
                            execution.completed_at = datetime.utcnow()
                            await session.commit()
                            return
                    raise HTTPException(status_code=400, detail=f"Flow execution is not in pending state: {execution.status}")
                
                # Update status to running
                execution.status = FlowExecutionStatus.RUNNING
                execution.started_at = datetime.utcnow()
                await session.commit()
                
                try:
                    # Get flow class
                    flow_class = self.get_flow_class(execution.flow_name)
                    if not flow_class:
                        raise ValueError(f"Flow {execution.flow_name} not found")
                        
                    # Initialize flow with state
                    flow = flow_class(state=execution.state)
                    
                    # Run flow
                    await flow.run()
                    
                    # Update status to completed
                    execution.status = FlowExecutionStatus.COMPLETED
                    execution.completed_at = datetime.utcnow()
                    await session.commit()
                    
                except Exception as e:
                    logger.error(f"Error running flow execution {execution_id}: {str(e)}", exc_info=True)
                    execution.status = FlowExecutionStatus.FAILED
                    execution.error = str(e)
                    execution.completed_at = datetime.utcnow()
                    await session.commit()
                    raise
                    
        except Exception as e:
            logger.error(f"Error starting flow execution {execution_id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
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
