import os
from dotenv import load_dotenv
import psycopg2
import uuid
from tabulate import tabulate
from ..config import get_db_password

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Database connection parameters
dbname = os.getenv('POSTGRES_DB', 'quizmaster')
user = os.getenv('POSTGRES_USER', 'postgres')
password = get_db_password()
host = os.getenv('POSTGRES_HOST', 'localhost')
port = os.getenv('POSTGRES_PORT', '5432')

# Expected mock user details
EXPECTED_USER_ID = '550e8400-e29b-41d4-a716-446655440000'
EXPECTED_USER_EMAIL = 'jkay65@gmail.com'
EXPECTED_USER_NAME = 'Development User'

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

    # Query all users
    cur.execute("SELECT id, email, name, created_at, updated_at FROM users")
    users = cur.fetchall()
    
    # Print all users in a table format
    headers = ['ID', 'Email', 'Name', 'Created At', 'Updated At']
    print("\nAll Users in Database:")
    print(tabulate(users, headers=headers, tablefmt='grid'))
    
    # Check for the specific mock user
    cur.execute("""
        SELECT id, email, name, created_at, updated_at 
        FROM users 
        WHERE id = %s OR email = %s
    """, (EXPECTED_USER_ID, EXPECTED_USER_EMAIL))
    
    mock_user = cur.fetchone()
    
    print("\nMock User Check:")
    if mock_user:
        user_id, email, name, created_at, updated_at = mock_user
        print(f"Found user in database:")
        print(f"  ID: {user_id}")
        print(f"  Email: {email}")
        print(f"  Name: {name}")
        print(f"  Created At: {created_at}")
        print(f"  Updated At: {updated_at}")
        
        # Verify if all expected values match
        matches = []
        matches.append(("ID", str(user_id) == EXPECTED_USER_ID))
        matches.append(("Email", email == EXPECTED_USER_EMAIL))
        matches.append(("Name", name == EXPECTED_USER_NAME))
        
        print("\nField Verification:")
        all_match = True
        for field, matches in matches:
            if matches:
                print(f"+ {field} matches expected value")
            else:
                print(f"- {field} does not match expected value")
                all_match = False
        
        if all_match:
            print("\n[SUCCESS] All fields match expected values!")
        else:
            print("\n[ERROR] Some fields do not match expected values")
    else:
        print("[ERROR] Mock user not found in database!")

except Exception as e:
    print(f"Error checking mock user: {str(e)}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
