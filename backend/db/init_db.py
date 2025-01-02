import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def init_database():
    # Database connection parameters
    dbname = os.getenv('POSTGRES_DB', 'quizmaster')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')

    # Create database if it doesn't exist
    conn = psycopg2.connect(
        dbname='postgres',
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Check if database exists
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (dbname,))
    exists = cur.fetchone()
    
    if not exists:
        print(f"Creating database {dbname}...")
        cur.execute(f'CREATE DATABASE {dbname}')
    
    cur.close()
    conn.close()

    # Connect to the target database and run migrations
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cur = conn.cursor()

    # Read and execute migration files
    migrations = [
        '001_initial_schema.sql',
        '002_add_mock_user.sql'
    ]
    
    for migration in migrations:
        migration_path = os.path.join(os.path.dirname(__file__), 'migrations', migration)
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
            print(f"Running migration {migration}...")
            cur.execute(migration_sql)

    # Insert development user if in mock auth mode
    if os.getenv('MOCK_AUTH') == 'true':
        print("Creating development user...")
        cur.execute("""
            INSERT INTO users (email, name)
            VALUES ('jkay65@gmail.com', 'Development User')
            ON CONFLICT (email) DO UPDATE
            SET name = EXCLUDED.name
            RETURNING id;
        """)
        dev_user_id = cur.fetchone()[0]
        print(f"Development user created with ID: {dev_user_id}")

    conn.commit()
    cur.close()
    conn.close()
    print("Database initialization completed successfully!")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"Error initializing database: {e}")
