from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import uuid
from datetime import datetime

class UserBase(BaseModel):
    """Base user model with common attributes"""
    email: EmailStr
    username: str
    
    class Config:
        orm_mode = True

class UserCreate(UserBase):
    """User registration model"""
    password: str
    display_name: Optional[str] = None

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    display_name: Optional[str] = None
    
    class Config:
        orm_mode = True

class UserResponse(UserBase):
    """User response model (for API returns)"""
    id: uuid.UUID
    display_name: Optional[str] = None
    created_at: datetime
    is_active: bool
    
    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class TokenData(BaseModel):
    """Token data model"""
    user_id: str
    expires_at: datetime