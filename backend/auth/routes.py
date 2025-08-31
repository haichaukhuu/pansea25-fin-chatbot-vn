from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any
import logging

from .models import (
    UserRegisterRequest, UserLoginRequest, RefreshTokenRequest,
    PasswordResetRequest, UpdateUserRequest, SetCustomClaimsRequest,
    AuthResponse, LoginResponse, UserResponse, TokenResponse, MessageResponse,
    TokenVerificationResponse, ErrorResponse, PasswordResetResponse
)
from .firebase_auth_service import firebase_auth_service
from .dependencies import get_current_user, require_admin, require_verified_email

logger = logging.getLogger(__name__)

# Create the auth router
auth_router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)

security = HTTPBearer()

@auth_router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegisterRequest):
    """
    Register a new user with email and password
    Returns user info with custom token for immediate authentication
    """
    try:
        user_info = await firebase_auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name
        )
        return AuthResponse(**user_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@auth_router.post("/login", response_model=LoginResponse)
async def login(user_data: UserLoginRequest):
    """
    Login user with email and password using Firebase Auth REST API
    Returns Firebase ID token, refresh token, and user information
    """
    try:
        auth_info = await firebase_auth_service.login_user(
            email=user_data.email,
            password=user_data.password
        )
        return LoginResponse(**auth_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )



@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: RefreshTokenRequest):
    """
    Generate a new custom token for the user
    """
    try:
        token_info = await firebase_auth_service.refresh_token(token_data.uid)
        return TokenResponse(**token_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@auth_router.post("/verify", response_model=TokenVerificationResponse)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify user's ID token and return user information
    """
    try:
        user_info = await firebase_auth_service.verify_id_token(credentials.credentials)
        return TokenVerificationResponse(**user_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )

@auth_router.post("/password-reset", response_model=PasswordResetResponse)
async def send_password_reset(reset_data: PasswordResetRequest):
    """
    Generate password reset link for user
    Note: In production, this link should be sent via email service
    """
    try:
        result = await firebase_auth_service.send_password_reset_email(reset_data.email)
        return PasswordResetResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate password reset link"
        )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user's information
    """
    try:
        user_info = await firebase_auth_service.get_user_by_uid(current_user['uid'])
        return UserResponse(**user_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@auth_router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UpdateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update current authenticated user's information
    """
    try:
        # Filter out None values
        update_kwargs = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if not update_kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        user_info = await firebase_auth_service.update_user(current_user['uid'], **update_kwargs)
        return UserResponse(**user_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user information"
        )

@auth_router.delete("/me", response_model=MessageResponse)
async def delete_current_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Delete current authenticated user's account
    """
    try:
        result = await firebase_auth_service.delete_user(current_user['uid'])
        return MessageResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )

# Admin-only endpoints
@auth_router.get("/admin/users/{uid}", response_model=UserResponse)
async def get_user_by_uid(
    uid: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Get user information by UID (Admin only)
    """
    try:
        user_info = await firebase_auth_service.get_user_by_uid(uid)
        return UserResponse(**user_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user by UID error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@auth_router.put("/admin/users/{uid}", response_model=UserResponse)
async def update_user_by_uid(
    uid: str,
    update_data: UpdateUserRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Update user information by UID (Admin only)
    """
    try:
        # Filter out None values
        update_kwargs = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if not update_kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        user_info = await firebase_auth_service.update_user(uid, **update_kwargs)
        return UserResponse(**user_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user by UID error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user information"
        )

@auth_router.delete("/admin/users/{uid}", response_model=MessageResponse)
async def delete_user_by_uid(
    uid: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Delete user account by UID (Admin only)
    """
    try:
        result = await firebase_auth_service.delete_user(uid)
        return MessageResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user by UID error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )

@auth_router.post("/admin/custom-claims", response_model=MessageResponse)
async def set_custom_claims(
    claims_data: SetCustomClaimsRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Set custom claims for a user (Admin only)
    """
    try:
        result = await firebase_auth_service.set_custom_claims(
            claims_data.uid,
            claims_data.claims
        )
        return MessageResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set custom claims error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set custom claims"
        )

@auth_router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """
    Logout user (client-side token invalidation)
    Note: Firebase tokens are stateless, so this is mainly for client cleanup
    """
    # In a real implementation, you might want to:
    # 1. Add the token to a blacklist (if you maintain one)
    # 2. Clear any server-side session data
    # 3. Invalidate refresh tokens (if you store them)
    
    # For now, we'll just return a success message
    # The client should remove the token from storage
    return MessageResponse(message="Logged out successfully. Please remove the token from client storage.")

# Health check endpoint for auth service
@auth_router.get("/health", response_model=MessageResponse)
async def auth_health_check():
    """
    Health check for authentication service
    """
    try:
        # Try to initialize Firebase (this will fail if not configured properly)
        firebase_auth_service.admin_auth
        return MessageResponse(message="Authentication service is healthy")
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not available"
        )
