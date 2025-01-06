from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Optional
from jwt import decode, PyJWTError, InvalidTokenError, ExpiredSignatureError
import os
import uuid
import logging
from uuid import UUID
from datetime import datetime, timedelta
import jwt

logger = logging.getLogger(__name__)

# Security scheme for bearer token
security = HTTPBearer()

# JWT configuration - use the same secret as NextAuth.js
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET")
if not NEXTAUTH_SECRET:
    logger.warning("NEXTAUTH_SECRET not set, using development secret")
    NEXTAUTH_SECRET = "development-secret"

async def verify_token(token: str) -> Optional[UUID]:
    """Verify JWT token and return user ID if valid."""
    try:
        # Remove Bearer prefix if present
        if token.startswith('Bearer '):
            token = token.replace('Bearer ', '')
            
        # Log token details for debugging
        logger.debug(f"Raw token: {token}")
        logger.debug(f"Token length: {len(token)}")
        logger.debug(f"Using JWT secret: {NEXTAUTH_SECRET[:5]}...")
            
        try:
            # First try to decode without verification to see the claims
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            logger.debug(f"Unverified token claims: {unverified_payload}")
        except Exception as e:
            logger.error(f"Could not decode token (even without verification): {str(e)}")
            
        # Now try to decode with verification
        payload = jwt.decode(
            token,
            NEXTAUTH_SECRET,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": False,  # NextAuth.js doesn't set exp claim
                "verify_iat": False,  # NextAuth.js handles iat differently
                "require": ["sub"]
            }
        )
        
        # Extract and validate user ID
        user_id = payload.get('sub')
        if not user_id:
            logger.warning("Token missing 'sub' claim")
            return None
            
        try:
            return UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid user ID format in token: {user_id}")
            return None
            
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}", exc_info=True)
        return None

async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> UUID:
    """Get current user from bearer token."""
    try:
        user_id = await verify_token(credentials.credentials)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return user_id
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
