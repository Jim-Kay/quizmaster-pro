from typing import AsyncGenerator
from fastapi import APIRouter, WebSocket, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from ..database import get_db
from ..models import FlowLog, LogLevel, FlowExecution as DBFlowExecution
from ..auth import get_current_user, verify_token
import json
import logging
from datetime import datetime
from urllib.parse import unquote

router = APIRouter()
logger = logging.getLogger(__name__)

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
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for streaming flow execution logs."""
    try:
        # Accept connection first to allow proper error responses
        await websocket.accept()
        
        # Log token details for debugging
        logger.debug(f"Raw token: {token}")
        logger.debug(f"Token length: {len(token) if token else 0}")
        
        # URL decode the token and remove Bearer prefix if present
        decoded_token = unquote(token)
        if decoded_token.startswith('Bearer '):
            decoded_token = decoded_token.replace('Bearer ', '')
        
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
            
        # Verify execution belongs to user
        try:
            stmt = select(DBFlowExecution).where(
                DBFlowExecution.id == execution_id,
                DBFlowExecution.user_id == user_id
            )
            result = await db.execute(stmt)
            execution = result.scalar_one_or_none()
            
            if not execution:
                logger.warning(f"Execution {execution_id} not found or does not belong to user {user_id}")
                await websocket.send_text(json.dumps({
                    "error": "Execution not found or does not belong to user"
                }))
                await websocket.close(code=4004)
                return
        except Exception as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            await websocket.send_text(json.dumps({
                "error": f"Database error: {str(e)}"
            }))
            await websocket.close(code=4005)
            return
            
        # First send existing logs
        try:
            logs = await get_logs(db, execution_id)
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

        # Listen for new logs using PostgreSQL LISTEN/NOTIFY
        async with db.connection() as conn:
            await conn.execute(text(f"LISTEN flow_logs_{execution_id}"))
            
            while True:
                try:
                    msg = await conn.driver_connection.notifies.get()
                    
                    try:
                        payload = json.loads(msg.payload)
                        if payload["execution_id"] == execution_id:
                            await websocket.send_json(payload["log"])
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in notification: {msg.payload}")
                        continue
                    except KeyError:
                        logger.warning(f"Missing required fields in notification: {msg.payload}")
                        continue
                except Exception as e:
                    logger.error(f"Error processing notification: {str(e)}", exc_info=True)
                    continue
                
    except Exception as e:
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

@router.get("/api/flows/executions/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all logs for a flow execution (REST fallback)."""
    return await get_logs(db, execution_id)
