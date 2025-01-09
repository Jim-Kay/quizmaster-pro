import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_enum():
    DB_USER = os.getenv("POSTGRES_USER", "test_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "test_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = "quizmaster_test"
    
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.connect() as conn:
        # Check enum type
        result = await conn.execute(text("SELECT unnest(enum_range(NULL::llmprovider))"))
        rows = result.fetchall()
        print("LLMProvider enum values in database:", [row[0] for row in rows])
        
        # Check user table
        result = await conn.execute(text("SELECT llm_provider FROM users"))
        rows = result.fetchall()
        print("\nLLMProvider values in users table:", [row[0] for row in rows])
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_enum())
