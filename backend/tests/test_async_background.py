import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy import Column, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import uuid
import httpx

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class TestModel(Base):
    __tablename__ = "test_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String(50), default="pending")
    result = Column(String, nullable=True)

app = FastAPI()

# Dependency to get database session
async def get_db():
    async with async_session() as session:
        yield session

async def background_task(item_id: str):
    """Simulate a long-running task with database operations"""
    try:
        logger.info(f"Starting background task for item {item_id}")
        await asyncio.sleep(2)  # Simulate some work
        
        async with async_session() as session:
            # This is where the SQLAlchemy error occurs in the real code
            result = await session.execute(
                select(TestModel).where(TestModel.id == item_id)
            )
            item = result.scalar_one()
            item.status = "completed"
            item.result = "Test result"
            await session.commit()
            
        logger.info(f"Background task completed for item {item_id}")
    except Exception as e:
        logger.error(f"Error in background task: {e}")
        async with async_session() as session:
            result = await session.execute(
                select(TestModel).where(TestModel.id == item_id)
            )
            item = result.scalar_one()
            item.status = "error"
            item.result = str(e)
            await session.commit()

@app.post("/test/items/create")
async def create_test_item(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a test item and start background processing"""
    try:
        # Create new test item
        item = TestModel(status="pending")
        db.add(item)
        await db.commit()
        await db.refresh(item)
        
        # Start background task
        background_tasks.add_task(background_task, item.id)
        
        return {"id": str(item.id), "status": item.status}
    except Exception as e:
        logger.error(f"Error creating test item: {e}")
        raise

@app.get("/test/items/{item_id}/status")
async def get_test_item_status(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the status of a test item"""
    result = await db.execute(
        select(TestModel).where(TestModel.id == item_id)
    )
    item = result.scalar_one()
    return {"id": str(item.id), "status": item.status, "result": item.result}

async def init_db():
    """Initialize the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def test_background_task():
    """Test the background task functionality"""
    logger.info("Starting test")
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Create test item
        response = await client.post("/test/items/create")
        assert response.status_code == 200
        data = response.json()
        item_id = data["id"]
        logger.info(f"Created test item: {item_id}")
        
        # Poll status until completion or error
        for _ in range(10):  # Poll for up to 10 seconds
            await asyncio.sleep(1)
            response = await client.get(f"/test/items/{item_id}/status")
            assert response.status_code == 200
            data = response.json()
            logger.info(f"Status: {data}")
            
            if data["status"] in ["completed", "error"]:
                break
        
        logger.info("Test completed")

if __name__ == "__main__":
    import uvicorn
    
    # Run the test
    asyncio.run(init_db())
    asyncio.run(test_background_task())
