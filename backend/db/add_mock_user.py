import os
from dotenv import load_dotenv
import psycopg2
import uuid
from ..config import get_db_password

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Database connection parameters
user = os.getenv('POSTGRES_USER', 'postgres')
password = get_db_password()
host = os.getenv('POSTGRES_HOST', 'localhost')
port = os.getenv('POSTGRES_PORT', '5432')

databases = [
    os.getenv('POSTGRES_DB', 'quizmaster'),
    os.getenv('TEST_DB_NAME', 'quizmaster_test')
]

# Insert mock user
mock_user_id = '550e8400-e29b-41d4-a716-446655440000'
mock_user_email = 'jkay65@gmail.com'
mock_user_name = 'Development User'

for dbname in databases:
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

        # First try to update existing user
        cur.execute("""
            UPDATE users 
            SET id = %s
            WHERE email = %s
            RETURNING id
        """, (mock_user_id, mock_user_email))
        
        if cur.fetchone() is None:
            # If no user exists with that email, insert new user
            cur.execute("""
                INSERT INTO users (id, email, name)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (mock_user_id, mock_user_email, mock_user_name))
        
        conn.commit()
        print(f"Mock user added/updated successfully in {dbname}!")
    except Exception as e:
        print(f"Error adding/updating mock user in {dbname}: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
