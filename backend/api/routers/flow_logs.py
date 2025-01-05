from typing import AsyncGenerator
from fastapi import APIRouter, WebSocket, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import FlowLog, LogLevel
from ..auth import get_current_user
from sqlalchemy import select, text
import json

router = APIRouter()

async def get_logs(db: AsyncSession, execution_id: str) -> list[dict]:
    """Get all logs for a flow execution."""
    result = await db.execute(
        select(FlowLog)
        .where(FlowLog.execution_id == execution_id)
        .order_by(FlowLog.timestamp)
    )
    logs = result.scalars().all()
    return [log.to_dict() for log in logs]

@router.websocket("/api/flows/executions/{execution_id}/logs/ws")
async def websocket_logs(
    websocket: WebSocket,
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    
    try:
        # First send existing logs
        logs = await get_logs(db, execution_id)
        for log in logs:
            await websocket.send_json(log)

        # Listen for new logs using PostgreSQL LISTEN/NOTIFY
        async with db.connection() as conn:
            await conn.execute(text("LISTEN flow_logs"))
            
            while True:
                msg = await conn.driver_connection.notifies.get()
                
                try:
                    payload = json.loads(msg.payload)
                    if payload["execution_id"] == execution_id:
                        await websocket.send_json(payload["log"])
                except json.JSONDecodeError:
                    continue
                except KeyError:
                    continue
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@router.get("/api/flows/executions/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all logs for a flow execution (REST fallback)."""
    return await get_logs(db, execution_id)
