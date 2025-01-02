from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from jwt import decode, PyJWTError, InvalidTokenError
import os
import uuid

# Create security scheme
security = HTTPBearer()

# Mock user ID for testing - using a proper UUID v4
MOCK_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

# Use the same secret as the frontend
JWT_SECRET = os.getenv("NEXTAUTH_SECRET", "development-secret")

async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> uuid.UUID:
    """Verify token and extract user ID based on auth mode"""
    try:
        if not credentials:
            raise HTTPException(status_code=401, detail="No credentials provided")
            
        token = credentials.credentials
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")

        # For mock auth, verify the token with the same secret
        try:
            payload = decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"]
            )
        except PyJWTError as e:
            print(f"Error decoding token: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
            
        return uuid.UUID(user_id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in auth: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
