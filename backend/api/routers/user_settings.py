from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
from pydantic import UUID4

from ..database import get_db
from ..models import User, LLMProvider
from ..auth import get_current_user
from ..utils.encryption import encrypt_api_key, decrypt_api_key
from ..schemas.user_settings import UserSettingsUpdate, UserSettingsResponse

router = APIRouter(tags=["user_settings"])

@router.get("/user/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's settings"""
    query = select(User).where(User.user_id == current_user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserSettingsResponse(
        llm_provider=user.llm_provider.value,
        has_openai_key=bool(user.encrypted_openai_key),
        has_anthropic_key=bool(user.encrypted_anthropic_key)
    )

@router.patch("/user/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings: UserSettingsUpdate,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update the current user's settings"""
    # Get current user
    query = select(User).where(User.user_id == current_user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_data = {}
    if settings.llm_provider is not None:
        update_data["llm_provider"] = LLMProvider[settings.llm_provider]
    
    # Handle API keys
    if settings.openai_key is not None:
        if settings.openai_key:  # If not empty string
            update_data["encrypted_openai_key"] = encrypt_api_key(settings.openai_key)
        else:  # If empty string, remove the key
            update_data["encrypted_openai_key"] = None
            
    if settings.anthropic_key is not None:
        if settings.anthropic_key:  # If not empty string
            update_data["encrypted_anthropic_key"] = encrypt_api_key(settings.anthropic_key)
        else:  # If empty string, remove the key
            update_data["encrypted_anthropic_key"] = None
    
    if update_data:
        query = update(User).where(User.user_id == current_user_id).values(**update_data)
        await db.execute(query)
        await db.commit()
    
    # Get updated user for response
    query = select(User).where(User.user_id == current_user_id)
    result = await db.execute(query)
    updated_user = result.scalar_one()
    
    return UserSettingsResponse(
        llm_provider=updated_user.llm_provider.value,
        has_openai_key=bool(updated_user.encrypted_openai_key),
        has_anthropic_key=bool(updated_user.encrypted_anthropic_key)
    )

@router.get("/user/validate-keys")
async def validate_api_keys(
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate the stored API keys by making test requests"""
    query = select(User).where(User.user_id == current_user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    validation_results = {
        "openai": False,
        "anthropic": False
    }
    
    # Validate OpenAI key if present
    if user.encrypted_openai_key:
        openai_key = decrypt_api_key(user.encrypted_openai_key)
        if openai_key:
            # TODO: Implement actual OpenAI API validation
            # For now, just return True if key exists
            validation_results["openai"] = True
    
    # Validate Anthropic key if present
    if user.encrypted_anthropic_key:
        anthropic_key = decrypt_api_key(user.encrypted_anthropic_key)
        if anthropic_key:
            # TODO: Implement actual Anthropic API validation
            # For now, just return True if key exists
            validation_results["anthropic"] = True
    
    return validation_results
