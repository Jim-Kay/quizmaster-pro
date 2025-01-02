"""
Non-pytest version of the blueprint API test.
This script tests the HTTP API endpoint for retrieving a specific blueprint by:
1. Setting up the test environment
2. Retrieving a specific blueprint with ID e25f9fa7-4348-4928-bd20-0cdb292dc18b
3. Verifying the response
"""

import os
import sys
from uuid import UUID
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.auth import MOCK_USER_ID
import psycopg2
from psycopg2.extras import DictCursor
import jwt
import logging
import asyncio
import json
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import uuid
import uvicorn
import subprocess
import time
import requests
import socket

from api.database import async_session_maker, Base, engine
from api.models import Topic, Blueprint, TerminalObjective, EnablingObjective, User

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Get database configuration from environment variables
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB", "quizmaster")  # Use main database instead of test
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "test-secret")  # Use a default test secret if env var not set

# Database URL for SQLAlchemy
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(process)d - %(filename)s-%(module)s:%(lineno)d - %(levelname)s: %(message)s'
)

# Create logger for this module
logger = logging.getLogger(__name__)

# API URL for testing
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Constants for topic and blueprint IDs
TOPIC_ID = UUID('519b6341-930e-44dd-948f-40229d7b4d07')
BLUEPRINT_ID = UUID('e25f9fa7-4348-4928-bd20-0cdb292dc18b')
USER_ID = UUID('550e8400-e29b-41d4-a716-446655440000')  # Use a consistent user ID

def create_jwt_token(user_id):
    """Create a mock JWT token for testing."""
    # Set expiration time
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Create JWT token with user ID
    token = jwt.encode(
        {
            "sub": str(user_id),  
            "exp": expiration
        },
        JWT_SECRET,  
        algorithm="HS256"
    )
    return token

async def check_database_connection():
    """Check database connection through SQLAlchemy."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT current_database();"))
            database = result.scalar()
            logger.info(f"Connected to database: {database}")

            result = await conn.execute(text("SELECT current_schema();"))
            schema = result.scalar()
            logger.info(f"Using schema: {schema}")

            result = await conn.execute(text("SELECT COUNT(*) FROM blueprints;"))
            count = result.scalar()
            logger.info(f"Number of blueprints: {count}")

            result = await conn.execute(text("SELECT blueprint_id, title FROM blueprints;"))
            blueprints = result.fetchall()
            for blueprint in blueprints:
                logger.info(f"Blueprint: {blueprint}")

            return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        return False

def check_database_direct():
    """Check database directly using psycopg2."""
    try:
        logger.info("Direct connection - Connecting to database...")
        logger.info(f"  Host: {DB_HOST}")
        logger.info(f"  Port: {DB_PORT}")
        logger.info(f"  Database: {DB_NAME}")
        logger.info(f"  User: {DB_USER}")
        
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Get database name
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()[0]
        logger.info(f"Direct connection - Connected to database: {db_name}")
        
        # Count blueprints
        cur.execute("SELECT COUNT(*) FROM blueprints;")
        count = cur.fetchone()[0]
        logger.info(f"Direct connection - Total blueprints: {count}")
        
        # Get specific blueprint
        blueprint_id = "e25f9fa7-4348-4928-bd20-0cdb292dc18b"
        cur.execute("""
            SELECT blueprint_id, title, topic_id, created_by, status 
            FROM blueprints 
            WHERE blueprint_id = %s;
        """, (blueprint_id,))
        blueprint = cur.fetchone()
        if blueprint:
            logger.info("Direct connection - Found blueprint:")
            logger.info(f"  ID: {blueprint['blueprint_id']}")
            logger.info(f"  Title: {blueprint['title']}")
            logger.info(f"  Topic ID: {blueprint['topic_id']}")
            logger.info(f"  Created by: {blueprint['created_by']}")
            logger.info(f"  Status: {blueprint['status']}")
            
            # Also get the topic
            cur.execute("""
                SELECT topic_id, title, created_by
                FROM topics
                WHERE topic_id = %s;
            """, (blueprint['topic_id'],))
            topic = cur.fetchone()
            if topic:
                logger.info("Direct connection - Found associated topic:")
                logger.info(f"  ID: {topic['topic_id']}")
                logger.info(f"  Title: {topic['title']}")
                logger.info(f"  Created by: {topic['created_by']}")
        else:
            logger.error("Direct connection - Blueprint not found")
        
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Direct connection - Error: {str(e)}")
        logger.error(f"Direct connection - Error type: {type(e)}")
        logger.error(f"Direct connection - Error args: {e.args}")

async def check_blueprint_exists(topic_id: UUID, blueprint_id: UUID):
    """Check if a blueprint exists in the database."""
    try:
        async with async_session_maker() as session:
            # Query for blueprint and include user_id
            query = select(Blueprint).where(
                Blueprint.blueprint_id == blueprint_id,
                Blueprint.topic_id == topic_id
            )
            result = await session.execute(query)
            blueprint = result.scalar_one_or_none()

            if blueprint:
                logger.info(f"Found blueprint: {blueprint.blueprint_id}")
                logger.info(f"Created by user: {blueprint.created_by}")
                return True, topic_id, blueprint.created_by
            else:
                logger.error(f"Blueprint not found: {blueprint_id}")
                return False, None, None
    except Exception as e:
        logger.error(f"Error checking blueprint: {str(e)}")
        return False, None, None

async def check_topic_exists(topic_id):
    """Check if topic exists in database directly."""
    async with async_session_maker() as session:
        try:
            # Get the topic
            query = select(Topic).where(Topic.topic_id == topic_id)
            result = await session.execute(query)
            topic = result.scalar_one_or_none()
            
            if topic:
                logger.info("Found topic:")
                logger.info(f"  ID: {topic.topic_id}")
                logger.info(f"  Title: {topic.title}")
                logger.info(f"  Created by: {topic.created_by}")
                return True, topic.created_by
            else:
                logger.error("Topic not found")
                return False, None
            
        except Exception as e:
            logger.error(f"Error checking topic: {str(e)}")
            return False, None

async def cleanup_test_data():
    """Clean up test data from previous runs."""
    async with async_session_maker() as session:
        try:
            # Delete test enabling objectives
            await session.execute(
                text("""
                    DELETE FROM enabling_objectives 
                    WHERE terminal_objective_id IN (
                        SELECT terminal_objective_id FROM terminal_objectives 
                        WHERE blueprint_id = :blueprint_id
                    )
                """),
                {"blueprint_id": "e25f9fa7-4348-4928-bd20-0cdb292dc18b"}
            )
            
            # Delete test terminal objectives
            await session.execute(
                text("""
                    DELETE FROM terminal_objectives 
                    WHERE blueprint_id = :blueprint_id
                """),
                {"blueprint_id": "e25f9fa7-4348-4928-bd20-0cdb292dc18b"}
            )
            
            # Delete test blueprint
            await session.execute(
                text("""
                    DELETE FROM blueprints 
                    WHERE blueprint_id = :blueprint_id
                """),
                {"blueprint_id": "e25f9fa7-4348-4928-bd20-0cdb292dc18b"}
            )
            
            # Delete test topic
            await session.execute(
                text("DELETE FROM topics WHERE title = 'Test Topic'")
            )
            
            await session.commit()
            logger.info("Cleaned up test data from previous runs")
        except Exception as e:
            logger.error(f"Error cleaning up test data: {str(e)}")
            await session.rollback()
            raise

async def create_test_data():
    """Create test data in the database."""
    try:
        async with async_session_maker() as session:
            # Create a test user
            user = User(
                user_id=USER_ID,
                email='jkay65@gmail.com',
                name='Test User',
                llm_provider="openai"
            )
            session.add(user)
            await session.flush()

            # Create a test topic
            topic = Topic(
                topic_id=TOPIC_ID,
                title='Test Topic',
                description='A test topic for testing',
                created_by=USER_ID
            )
            session.add(topic)
            await session.flush()

            # Create a test blueprint
            blueprint = Blueprint(
                blueprint_id=BLUEPRINT_ID,
                title='Test Blueprint',
                description='A test blueprint',
                status='completed',
                created_at=datetime.now(timezone.utc),
                created_by=USER_ID,
                topic_id=TOPIC_ID,
                terminal_objectives_count=1,
                enabling_objectives_count=2
            )
            session.add(blueprint)
            await session.flush()

            # Create a test terminal objective
            terminal_obj = TerminalObjective(
                terminal_objective_id=uuid.uuid4(),
                title='Test Terminal Objective',
                number=1,
                description='Test Terminal Objective',
                cognitive_level='UNDERSTAND',
                blueprint_id=BLUEPRINT_ID,
                topic_id=TOPIC_ID
            )
            session.add(terminal_obj)
            await session.flush()

            # Create test enabling objectives
            enabling_obj1 = EnablingObjective(
                enabling_objective_id=uuid.uuid4(),
                title='Test Enabling Objective 1',
                number='1.1',
                description='Test Enabling Objective 1',
                cognitive_level='UNDERSTAND',
                terminal_objective_id=terminal_obj.terminal_objective_id
            )
            session.add(enabling_obj1)

            enabling_obj2 = EnablingObjective(
                enabling_objective_id=uuid.uuid4(),
                title='Test Enabling Objective 2',
                number='1.2',
                description='Test Enabling Objective 2',
                cognitive_level='UNDERSTAND',
                terminal_objective_id=terminal_obj.terminal_objective_id
            )
            session.add(enabling_obj2)

            await session.commit()
            logger.info("Successfully created test data")
    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
        await session.rollback()
        raise

async def setup_database():
    """Setup database tables."""
    try:
        # Create tables
        async with engine.begin() as conn:
            # Drop all tables with CASCADE
            await conn.execute(text("DROP TABLE IF EXISTS objectives CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS enabling_objectives CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS terminal_objectives CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS blueprints CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS topics CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Created database tables")
            
            # Create enum types if they don't exist
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE llmprovider AS ENUM ('openai', 'anthropic');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            logger.info("Setup database completed successfully")
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        raise

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

async def wait_for_server(url: str, max_retries: int = 10, delay: float = 2.0):
    """Wait for the server to be ready."""
    health_url = f"{url}/api/health"
    for i in range(max_retries):
        try:
            response = requests.get(health_url)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    logger.info("Server is healthy and ready")
                    return True
            logger.info(f"Server returned status {response.status_code}, waiting...")
        except requests.exceptions.ConnectionError:
            logger.info(f"Server not ready (attempt {i+1}/{max_retries}), retrying in {delay} seconds...")
            time.sleep(delay)
    return False

async def run_test():
    """Run the test."""
    try:
        # Check database connection
        await check_database_connection()
        
        # Use constants for topic and blueprint IDs
        topic_id = TOPIC_ID
        blueprint_id = BLUEPRINT_ID
        
        # Check if blueprint exists and get user ID
        exists, topic_id, user_id = await check_blueprint_exists(topic_id, blueprint_id)
        if not exists:
            logger.error("Blueprint does not exist in database")
            return

        server = None
        server_started = False

        try:
            # Check if server is already running
            if is_port_in_use(8000):
                logger.info("Server already running on port 8000")
            else:
                # Start the FastAPI server
                logger.info("Starting FastAPI server...")
                server = subprocess.Popen(["uvicorn", "backend.api.main:app", "--port", "8000"])
                server_started = True
            
            # Wait for the server to be ready
            if not await wait_for_server(API_URL):
                logger.error("Server failed to start after multiple retries")
                return

            # Create test client with the correct user ID
            async with AsyncClient(transport=ASGITransport(app=app), base_url=API_URL) as client:
                # Set up authentication token with the correct user ID
                token_data = {
                    "sub": str(USER_ID),
                    "exp": datetime.now(timezone.utc) + timedelta(hours=1)
                }
                token = jwt.encode(token_data, JWT_SECRET, algorithm="HS256")
                headers = {"Authorization": f"Bearer {token}"}
                logger.info(f"Using auth token: {token}")
                logger.info(f"Using headers: {headers}")
                
                # Test getting specific blueprint using correct endpoint path
                url = f"/api/topics/{topic_id}/blueprints/{blueprint_id}"
                logger.info(f"Making request to: {url}")
                response = await client.get(url, headers=headers)
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                logger.info(f"Response content: {response.text}")
                
                if response.status_code == 200:
                    blueprint = response.json()
                    logger.info("Successfully retrieved blueprint:")
                    logger.info(f"  ID: {blueprint.get('blueprint_id')}")
                    logger.info(f"  Title: {blueprint.get('title')}")
                    logger.info(f"  Topic ID: {blueprint.get('topic_id')}")
                else:
                    logger.error(f"Failed to retrieve blueprint. Status code: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    
                    # Try getting all blueprints for the topic
                    all_url = f"/api/topics/{topic_id}/blueprints"
                    logger.info(f"Trying to get all blueprints for topic. URL: {all_url}")
                    all_response = await client.get(all_url, headers=headers)
                    logger.info(f"All blueprints response status: {all_response.status_code}")
                    if all_response.status_code == 200:
                        blueprints = all_response.json()
                        logger.info(f"Found {len(blueprints)} blueprints for topic")
                        for bp in blueprints:
                            logger.info(f"  {bp.get('blueprint_id')}: {bp.get('title')}")
        finally:
            # Only stop the server if we started it
            if server and server_started:
                logger.info("Stopping FastAPI server...")
                server.terminate()
                server.wait()

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

async def main():
    """Main entry point."""
    try:
        # Create test data first
        await setup_database()
        await create_test_data()
        
        # Run the test
        await run_test()
        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise
    finally:
        # Close any remaining connections
        await create_async_engine(DATABASE_URL, echo=True).dispose()

if __name__ == "__main__":
    asyncio.run(main())
