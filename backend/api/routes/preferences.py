"""
API routes for user preferences management

This module provides REST API endpoints for managing user preferences stored in DynamoDB.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from api.middleware.auth_middleware import get_current_user
from core.services.dynamodb_service import dynamodb_service
from database.models.dynamodb_models import (
    PreferenceCreateRequest,
    PreferenceUpdateRequest,
    PreferenceResponse
)
from database.models.user import User

logger = logging.getLogger(__name__)

# Create router for preferences endpoints
preferences_router = APIRouter(prefix="/preferences", tags=["preferences"])


@preferences_router.post("/", response_model=PreferenceResponse)
def create_user_preferences(
    preference_data: PreferenceCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create new user preferences after onboarding.
    
    This endpoint is called when a user completes the onboarding questionnaire.
    It stores their preferences in DynamoDB for personalization.
    
    Args:
        preference_data: The questionnaire answers from frontend
        current_user: The authenticated user from JWT token
        
    Returns:
        PreferenceResponse: Success/failure status with preference data
        
    Raises:
        HTTPException: 400 for validation errors, 409 for conflicts, 500 for server errors
    """
    try:
        logger.info(f"Creating preferences for user {current_user.id}")
        
        # Create preferences using the service
        result = dynamodb_service.create_user_preference(
            user_id=str(current_user.id),
            preference_data=preference_data
        )
        
        if result['success']:
            logger.info(f"Successfully created preferences for user {current_user.id}")
            return PreferenceResponse(**result)
        else:
            # Handle business logic failures
            if "already exist" in result['message']:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=result['message']
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result['message']
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating preferences"
        )


@preferences_router.get("/", response_model=PreferenceResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's preferences.
    
    This endpoint retrieves the user's stored preferences from DynamoDB.
    
    Args:
        current_user: The authenticated user from JWT token
        
    Returns:
        PreferenceResponse: User's preference data
        
    Raises:
        HTTPException: 404 if not found, 500 for server errors
    """
    try:
        logger.info(f"Getting preferences for user {current_user.id}")
        
        # Get preferences using the service
        result = dynamodb_service.get_user_preference(str(current_user.id))
        
        if result['success']:
            logger.info(f"Successfully retrieved preferences for user {current_user.id}")
            return PreferenceResponse(**result)
        else:
            if "not found" in result['message']:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User preferences not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result['message']
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving preferences"
        )


@preferences_router.put("/", response_model=PreferenceResponse)
def update_user_preferences(
    preference_data: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's preferences.
    
    This endpoint allows users to modify their preferences after initial setup.
    
    Args:
        preference_data: The updated questionnaire answers
        current_user: The authenticated user from JWT token
        
    Returns:
        PreferenceResponse: Updated preference data
        
    Raises:
        HTTPException: 404 if not found, 400 for validation errors, 500 for server errors
    """
    try:
        logger.info(f"Updating preferences for user {current_user.id}")
        
        # Update preferences using the service
        result = dynamodb_service.update_user_preference(
            user_id=str(current_user.id),
            preference_data=preference_data
        )
        
        if result['success']:
            logger.info(f"Successfully updated preferences for user {current_user.id}")
            return PreferenceResponse(**result)
        else:
            if "not found" in result['message']:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User preferences not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result['message']
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating preferences"
        )


@preferences_router.delete("/", response_model=PreferenceResponse)
def delete_user_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Delete current user's preferences.
    
    This endpoint allows users to remove their stored preferences.
    
    Args:
        current_user: The authenticated user from JWT token
        
    Returns:
        PreferenceResponse: Deletion status
        
    Raises:
        HTTPException: 404 if not found, 500 for server errors
    """
    try:
        logger.info(f"Deleting preferences for user {current_user.id}")
        
        # Delete preferences using the service
        result = dynamodb_service.delete_user_preference(str(current_user.id))
        
        if result['success']:
            logger.info(f"Successfully deleted preferences for user {current_user.id}")
            return PreferenceResponse(**result)
        else:
            if "not found" in result['message']:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User preferences not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result['message']
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting preferences"
        )


@preferences_router.post("/upsert", response_model=PreferenceResponse)
def upsert_user_preferences(
    preference_data: PreferenceCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create or update user preferences (upsert operation).
    
    This endpoint creates new preferences if they don't exist, or updates existing ones.
    This is useful for the onboarding flow to handle both new and returning users.
    
    Args:
        preference_data: The questionnaire answers from frontend
        current_user: The authenticated user from JWT token
        
    Returns:
        PreferenceResponse: Preference data after upsert
        
    Raises:
        HTTPException: 400 for validation errors, 500 for server errors
    """
    try:
        logger.info(f"Upserting preferences for user {current_user.id}")
        
        # Upsert preferences using the service
        result = dynamodb_service.upsert_user_preference(
            user_id=str(current_user.id),
            preference_data=preference_data
        )
        
        if result['success']:
            logger.info(f"Successfully upserted preferences for user {current_user.id}")
            return PreferenceResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error upserting preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while upserting preferences"
        )


@preferences_router.get("/exists")
def check_preferences_exist(
    current_user: User = Depends(get_current_user)
):
    """
    Check if user preferences exist.
    
    This endpoint checks whether the user has completed the onboarding questionnaire.
    Useful for frontend to determine whether to show onboarding or main app.
    
    Args:
        current_user: The authenticated user from JWT token
        
    Returns:
        dict: Boolean indicating if preferences exist
        
    Raises:
        HTTPException: 500 for server errors
    """
    try:
        logger.info(f"Checking preferences existence for user {current_user.id}")
        
        # Check if preferences exist
        exists = dynamodb_service.check_preference_exists(str(current_user.id))
        
        logger.info(f"Preferences exist for user {current_user.id}: {exists}")
        
        return {
            "exists": exists,
            "user_id": str(current_user.id),
            "message": "Preferences found" if exists else "No preferences found"
        }
    
    except Exception as e:
        logger.error(f"Unexpected error checking preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking preferences"
        )


@preferences_router.get("/health")
def preferences_health_check():
    """
    Health check endpoint for preferences service.
    
    This endpoint checks the health of DynamoDB connection and the Preference table.
    
    Returns:
        dict: Health status information
    """
    try:
        from database.connections.dynamodb_connection import get_dynamodb_health
        
        health_status = get_dynamodb_health()
        
        if health_status['status'] == 'healthy':
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=health_status
            )
        elif health_status['status'] == 'warning':
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=health_status
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=health_status
            )
    
    except Exception as e:
        logger.error(f"Error during preferences health check: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "message": "Preferences service is not available"
            }
        )
