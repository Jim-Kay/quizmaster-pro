import os
from dotenv import load_dotenv
from ..config import get_db_password
import psycopg2

# Load environment variables
load_dotenv()

# Database connection parameters
dbname = os.getenv('POSTGRES_DB', 'quizmaster')
user = os.getenv('POSTGRES_USER', 'postgres')
password = get_db_password()
host = os.getenv('POSTGRES_HOST', 'localhost')
port = os.getenv('POSTGRES_PORT', '5432')

try:
    # Connect to the database
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cur = conn.cursor()
    
    # Create alembic_version table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) PRIMARY KEY
        );
    """)
    
    # Insert the version
    cur.execute("""
        INSERT INTO alembic_version (version_num)
        VALUES ('c73eb45ffe0e')
        ON CONFLICT (version_num) DO NOTHING;
    """)
    
    conn.commit()
    print("Migration marked as complete!")
except Exception as e:
    print(f"Error marking migration: {str(e)}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
