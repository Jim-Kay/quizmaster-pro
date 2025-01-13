"""Developer testing routes for QuizMasterPro."""
from typing import Optional
import asyncio
import time
from fastapi import APIRouter, WebSocket, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..auth import get_current_user, verify_token, MOCK_USER_ID
from ..core.models import User
from ..core.config import get_settings

router = APIRouter(prefix="/dev", tags=["developer"])

# Get settings instance
settings = get_settings()

class SimulationConfig(BaseModel):
    """Configuration for WebSocket simulation."""
    duration_seconds: int
    frequency_seconds: float
    message_prefix: Optional[str] = "Test message"

@router.websocket("/ws/test")
async def websocket_test(websocket: WebSocket, token: str):
    """WebSocket endpoint for testing long-running processes."""
    try:
        # Accept the connection first
        await websocket.accept()
        print("WebSocket connection accepted")

        # Send initial connection message
        await websocket.send_json({
            "type": "test",
            "message": "Connection successful"
        })

        # Keep the connection open and handle simulation
        while True:
            try:
                data = await websocket.receive_json()
                print(f"Received config: {data}")
                
                # Parse simulation config
                config = SimulationConfig(**data)
                
                # Send simulation start message
                await websocket.send_json({
                    "type": "simulation_started",
                    "message": "Starting simulation",
                    "config": data
                })

                # Run simulation
                start_time = time.time()
                message_count = 0
                
                while time.time() - start_time < config.duration_seconds:
                    message_count += 1
                    elapsed = time.time() - start_time
                    remaining = config.duration_seconds - elapsed
                    
                    await websocket.send_json({
                        "type": "simulation_update",
                        "message": f"{config.message_prefix} #{message_count}",
                        "elapsed_seconds": round(elapsed, 2),
                        "remaining_seconds": round(remaining, 2)
                    })
                    
                    await asyncio.sleep(config.frequency_seconds)
                
                # Send completion message
                await websocket.send_json({
                    "type": "simulation_complete",
                    "total_messages": message_count,
                    "duration_seconds": round(time.time() - start_time, 2)
                })

            except Exception as e:
                print(f"Error handling message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        if websocket.client_state.value == 0:  # WebSocket not yet accepted
            await websocket.accept()
        await websocket.close(code=status.HTTP_500_INTERNAL_SERVER_ERROR)
