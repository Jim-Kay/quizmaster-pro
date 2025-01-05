import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import FlowLog, LogLevel
from ..database import async_session_maker

class DatabaseLogger(logging.Logger):
    """A logger that writes to both the database and standard output."""
    
    def __init__(self, name: str, execution_id: UUID):
        super().__init__(name)
        self.execution_id = execution_id
        self._log_queue = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._worker_task = None

    async def start_worker(self):
        """Start the async worker that processes logs."""
        self._worker_task = asyncio.create_task(self._process_logs())

    async def stop_worker(self):
        """Stop the async worker."""
        if self._worker_task:
            self._stop_event.set()
            await self._worker_task

    async def _process_logs(self):
        """Process logs from the queue and write to database."""
        async with async_session_maker() as session:
            while not self._stop_event.is_set():
                try:
                    # Get all available logs (up to 100 at a time)
                    logs = []
                    for _ in range(100):
                        try:
                            log = self._log_queue.get_nowait()
                            logs.append(log)
                        except asyncio.QueueEmpty:
                            break

                    if logs:
                        # Bulk insert logs
                        await session.execute(
                            insert(FlowLog),
                            [log.dict() for log in logs]
                        )
                        await session.commit()

                        # Notify subscribers
                        for log in logs:
                            await self._notify_subscribers(session, log)

                    # Small delay to prevent tight loop
                    await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"Error processing logs: {e}")
                    await asyncio.sleep(1)  # Longer delay on error

    async def _notify_subscribers(self, session: AsyncSession, log: FlowLog):
        """Notify subscribers of new log entries using PostgreSQL NOTIFY."""
        notification = {
            "execution_id": str(self.execution_id),
            "log": log.to_dict()
        }
        await session.execute(
            f"SELECT pg_notify('flow_logs', :payload)",
            {"payload": notification}
        )

    async def alog(self, level: LogLevel, msg: str, metadata: Optional[Dict[str, Any]] = None):
        """Async log method that queues logs for processing."""
        log_entry = FlowLog(
            execution_id=self.execution_id,
            timestamp=datetime.utcnow(),
            level=level,
            message=msg,
            log_metadata=metadata
        )
        await self._log_queue.put(log_entry)
        # Also print to stdout for debugging
        print(f"[{level.value.upper()}] {msg}")

    async def adebug(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        await self.alog(LogLevel.DEBUG, msg, metadata)

    async def ainfo(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        await self.alog(LogLevel.INFO, msg, metadata)

    async def awarning(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        await self.alog(LogLevel.WARNING, msg, metadata)

    async def aerror(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        await self.alog(LogLevel.ERROR, msg, metadata)

    # Sync methods that create tasks for async logging
    def log(self, level: LogLevel, msg: str, metadata: Optional[Dict[str, Any]] = None):
        asyncio.create_task(self.alog(level, msg, metadata))

    def debug(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        asyncio.create_task(self.adebug(msg, metadata))

    def info(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        asyncio.create_task(self.ainfo(msg, metadata))

    def warning(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        asyncio.create_task(self.awarning(msg, metadata))

    def error(self, msg: str, metadata: Optional[Dict[str, Any]] = None):
        asyncio.create_task(self.aerror(msg, metadata))
