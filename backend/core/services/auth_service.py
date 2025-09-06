import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import uuid
import logging
from database.repositories.user_repository import UserRepository
from core.models.user import UserCreate, UserLogin, UserResponse, TokenData
from config import Config

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for user login and registration"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.secret_key = Config.JWT_SECRET_KEY
        self.algorithm = Config.JWT_ALGORITHM
        self.access_token_expire_minutes = Config.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = Config.REFRESH_TOKEN_EXPIRE_DAYS
        
    def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user."""
        try:
            # Check if user with this email already exists
            if self.user_repository.get_user_by_email(user_data.email):
                logger.warning(f"Registration attempt with existing email: {user_data.email}")
                raise ValueError("User with this email already exists")
                
            # Check if username is taken
            if self.user_repository.get_user_by_username(user_data.username):
                logger.warning(f"Registration attempt with existing username: {user_data.username}")
                raise ValueError("Username is already taken")
                
            # Create the user
            user = self.user_repository.create_user(user_data)
            logger.info(f"Successfully registered user: {user.email}")
            return UserResponse.from_orm(user)
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise
    
    def authenticate_user(self, login_data: UserLogin) -> Optional[UserResponse]:
        """Authenticate a user by email and password."""
        try:
            user = self.user_repository.get_user_by_email(login_data.email)
            if not user:
                logger.warning(f"Login attempt with non-existent email: {login_data.email}")
                return None
                
            if not self.user_repository.verify_password(user, login_data.password):
                logger.warning(f"Failed login attempt for user: {login_data.email}")
                return None
                
            logger.info(f"Successful login for user: {login_data.email}")
            return UserResponse.from_orm(user)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise
    
    def create_access_token(self, user_id: uuid.UUID) -> str:
        """Create JWT access token."""
        try:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            to_encode = {
                "sub": str(user_id),
                "exp": expire
            }
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation error: {str(e)}")
            raise
    
    def create_refresh_token(self, user_id: uuid.UUID) -> str:
        """Create JWT refresh token."""
        try:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            to_encode = {
                "sub": str(user_id),
                "exp": expire,
                "refresh": True
            }
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Refresh token creation error: {str(e)}")
            raise
    
    def verify_token(self, token: str) -> Optional[uuid.UUID]:
        """Verify JWT token and return user ID if valid."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                logger.warning("Token verification failed: missing user ID")
                return None
            return uuid.UUID(user_id)
        except jwt.PyJWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected token verification error: {str(e)}")
            return None
    
    def get_token_data(self, token: str) -> Optional[TokenData]:
        """Get token data including expiration."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                return None
            expires_at = datetime.fromtimestamp(payload.get("exp"))
            return TokenData(user_id=user_id, expires_at=expires_at)
        except Exception:
            return None