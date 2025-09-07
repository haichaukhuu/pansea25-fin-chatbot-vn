from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging
from typing import Dict

from core.models.user import UserCreate, UserLogin, UserResponse
from core.services.auth_service import AuthService
from database.repositories.user_repository import UserRepository
from database.connections.rds_postgres import postgres_connection

logger = logging.getLogger(__name__)

# Create router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_db():
    """Get database session"""
    db = postgres_connection.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_auth_service(db: Session = Depends(get_db)):
    """Get authentication service"""
    user_repository = UserRepository(db)
    return AuthService(user_repository)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Get current authenticated user from token"""
    user_id = auth_service.verify_token(token)
    if user_id is None:
        logger.warning("Invalid authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = UserRepository(db).get_user_by_id(user_id)
    if user is None:
        logger.warning(f"User not found for ID from token: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserResponse.from_orm(user)

@auth_router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        logger.info(f"Registration attempt with data: {user_data.dict()}")
        return auth_service.register_user(user_data)
    except ValueError as e:
        logger.warning(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@auth_router.post("/login", response_model=Dict[str, str])
async def login(
    user_data: UserLogin,  # Use your UserLogin model instead of OAuth2PasswordRequestForm
    auth_service: AuthService = Depends(get_auth_service),
    response: Response = None
):
    """Login and get access token"""
    try:
        logger.info(f"Login attempt for email: {user_data.email}")
        # Already using UserLogin model, so no need to create it
        user = auth_service.authenticate_user(user_data)
        
        if not user:
            logger.warning(f"Failed login attempt for: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = auth_service.create_access_token(user.id)
        
        # Create refresh token
        refresh_token = auth_service.create_refresh_token(user.id)
        
        # Set refresh token in HTTP-only cookie
        if response:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,  # Use in production with HTTPS
                samesite="strict"
            )
        
        logger.info(f"Successful login for: {user_data.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user.id)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@auth_router.post("/refresh")
async def refresh_token(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
    refresh_token: str = Depends(lambda r: r.cookies.get("refresh_token"))
):
    """Refresh access token using refresh token"""
    try:
        if not refresh_token:
            logger.warning("Refresh token missing in request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is required",
            )
        
        # Verify the refresh token
        user_id = auth_service.verify_token(refresh_token)
        if not user_id:
            logger.warning("Invalid refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Check if user exists
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            logger.warning(f"User not found for refresh token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        # Create new access token
        access_token = auth_service.create_access_token(user.id)
        
        # Create new refresh token
        new_refresh_token = auth_service.create_refresh_token(user.id)
        
        # Update cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="strict"
        )
        
        logger.info(f"Token refreshed for user ID: {user_id}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@auth_router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@auth_router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing refresh token"""
    response.delete_cookie(key="refresh_token")
    logger.info("User logged out")
    return {"message": "Logged out successfully"}