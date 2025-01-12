"""Authentication utilities"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .core.config import get_settings
from .core.database import get_db, get_session
from .core.models import User

# Get settings instance
settings = get_settings()

# Mock user ID for testing
MOCK_USER_ID = UUID('f9b5645d-898b-4d58-b10a-a6b50a9d234b')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# Security scheme for bearer token
security = OAuth2PasswordBearer(tokenUrl="/api/token")

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token"""
    to_encode = data.copy()
    
    # Convert UUID to string if present
    if 'sub' in to_encode and isinstance(to_encode['sub'], UUID):
        to_encode['sub'] = str(to_encode['sub'])
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.auth_secret, algorithm=settings.auth_algorithm)
    return encoded_jwt

async def verify_token(token: str, db: AsyncSession) -> Optional[User]:
    """Verify a JWT token and return the user"""
    try:
        payload = jwt.decode(token, settings.auth_secret, algorithms=[settings.auth_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            return None
            
        # Convert string to UUID
        try:
            user_id = UUID(user_id)
        except ValueError:
            return None
        
        # Use provided session to get user
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user
    except jwt.PyJWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from token"""
    user = await verify_token(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Get password hash"""
    return pwd_context.hash(password)
