"""Test configuration and fixtures."""
import asyncio
import pytest
import subprocess
import time
import requests
from typing import AsyncGenerator, Generator
import psutil
import signal
import os

def find_process_by_port(port: int) -> list[int]:
    """Find process IDs using the specified port."""
    pids = []
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            pids.append(conn.pid)
    return pids

def kill_process_tree(pid: int) -> None:
    """Kill a process and all its children."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
    except psutil.NoSuchProcess:
        pass

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_environment(request) -> Generator[None, None, None]:
    """Start the test environment and cleanup after tests."""
    # Environment variables for test
    os.environ["QUIZMASTER_ENVIRONMENT"] = "test"
    os.environ["TEST_MODE"] = "true"
    os.environ["NODE_ENV"] = "test"

    # Only start services for integration tests
    if "integration" in request.node.name:
        # Start backend
        backend_process = subprocess.Popen(
            ["uvicorn", "api.main:app", "--reload", "--port", "8000"],
            cwd="backend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for backend to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:8000/api/health")
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
            if attempt == max_attempts - 1:
                raise Exception("Backend failed to start")

        # Start frontend
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev", "--", "-p", "3000"],
            cwd="frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for frontend to be ready
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:3000")
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
            if attempt == max_attempts - 1:
                raise Exception("Frontend failed to start")

    yield

    # Cleanup
    if "integration" in request.node.name:
        # Kill processes by port
        for port in [8000, 3000]:
            for pid in find_process_by_port(port):
                kill_process_tree(pid)

@pytest.fixture(scope="session")
async def test_db():
    """Create test database and tables."""
    from api.core.database import get_engine, Base
    
    engine = await get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_db) -> AsyncGenerator:
    """Create a new database session for a test."""
    from api.core.database import async_session_maker
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
        
@pytest.fixture(autouse=True)
def _setup_testing_environment(monkeypatch):
    """Setup environment variables for testing."""
    monkeypatch.setenv("QUIZMASTER_ENVIRONMENT", "test")
    monkeypatch.setenv("TEST_MODE", "true")
