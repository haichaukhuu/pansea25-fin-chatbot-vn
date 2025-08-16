"""
Firebase Authentication Module

This module provides Firebase authentication functionality for the AgriFinHub application.
It includes user registration, login, token verification, and user management capabilities.

Components:
- firebase_config: Firebase SDK configuration and initialization
- firebase_auth_service: Core authentication service
- dependencies: FastAPI dependencies for authentication
- models: Pydantic models for request/response schemas
- routes: API endpoints for authentication

Usage:
    from backend.auth import auth_router
    app.include_router(auth_router)
"""

from .firebase_config import firebase_config
from .firebase_auth_service import firebase_auth_service
from .dependencies import get_current_user, get_optional_user, require_admin, require_verified_email
from .routes import auth_router
from .models import (
    UserRegisterRequest, UserLoginRequest, RefreshTokenRequest,
    PasswordResetRequest, UpdateUserRequest, SetCustomClaimsRequest,
    AuthResponse, UserResponse, TokenResponse, MessageResponse,
    TokenVerificationResponse, ErrorResponse
)

__all__ = [
    "firebase_config",
    "firebase_auth_service", 
    "get_current_user",
    "get_optional_user",
    "require_admin",
    "require_verified_email",
    "auth_router",
    "UserRegisterRequest",
    "UserLoginRequest", 
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "UpdateUserRequest",
    "SetCustomClaimsRequest",
    "AuthResponse",
    "UserResponse",
    "TokenResponse",
    "MessageResponse",
    "TokenVerificationResponse",
    "ErrorResponse"
]
