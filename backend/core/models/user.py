from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    """Model for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = None
        
    @validator('password')
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v

class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    display_name: Optional[str] = None

class UserResponse(BaseModel):
    """Model for user responses"""
    id: uuid.UUID
    email: str
    display_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    # class Config:
    #     from_attributes = True

    model_config = {
        "from_attributes": True
    }

class TokenData(BaseModel):
    """Model for token data"""
    user_id: str
    expires_at: datetime