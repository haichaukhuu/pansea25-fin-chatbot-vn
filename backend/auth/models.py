from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

# Request Models
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    display_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str



class RefreshTokenRequest(BaseModel):
    uid: str  # Changed from refresh_token to uid since we're using custom tokens

class PasswordResetRequest(BaseModel):
    email: EmailStr

class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = None
    photo_url: Optional[str] = None

class SetCustomClaimsRequest(BaseModel):
    uid: str
    claims: Dict[str, Any]

# Response Models
class UserResponse(BaseModel):
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    email_verified: bool
    phone_number: Optional[str] = None
    photo_url: Optional[str] = None
    disabled: Optional[bool] = False
    created_at: Optional[datetime] = None
    last_sign_in: Optional[datetime] = None
    custom_claims: Optional[Dict[str, Any]] = {}

class AuthResponse(BaseModel):
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    email_verified: bool
    custom_token: str
    message: Optional[str] = None

class LoginResponse(BaseModel):
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    email_verified: bool
    id_token: str
    refresh_token: str
    expires_in: str
    message: Optional[str] = None

class TokenResponse(BaseModel):
    custom_token: str
    uid: str
    message: Optional[str] = None

class PasswordResetResponse(BaseModel):
    message: str
    reset_link: str
    note: Optional[str] = None

class MessageResponse(BaseModel):
    message: str

class TokenVerificationResponse(BaseModel):
    uid: str
    email: Optional[str]
    email_verified: bool
    display_name: Optional[str]
    auth_time: Optional[int]
    iat: Optional[int]
    exp: Optional[int]
    firebase: Optional[Dict[str, Any]] = {}

# Error Models
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

# Additional Models for extended functionality
class UserListResponse(BaseModel):
    users: list[UserResponse]
    total_count: int
    page: int
    per_page: int

class CustomClaimsResponse(BaseModel):
    uid: str
    custom_claims: Dict[str, Any]
