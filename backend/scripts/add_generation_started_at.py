import asyncio
import sys
import os

# Add parent directory to path so we can import from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import add_generation_started_at_column

async def main():
    await add_generation_started_at_column()

if __name__ == "__main__":
    asyncio.run(main())
