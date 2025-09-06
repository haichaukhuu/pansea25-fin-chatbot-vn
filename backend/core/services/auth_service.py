import jwt
from datetime import datetime, timedelta
from typing import Optional
import uuid
from database.repositories.user_repository import UserRepository
from core.models.user import UserCreate, UserLogin, UserResponse
from config import Config

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.secret_key = Config.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.token_expire_minutes = 60 * 24  # 24 hours
        
    def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user."""
        # Check if user with this email already exists
        if self.user_repository.get_user_by_email(user_data.email):
            raise ValueError("User with this email already exists")
            
        # Check if username is taken
        if self.user_repository.get_user_by_username(user_data.username):
            raise ValueError("Username is already taken")
            
        # Create the user
        user = self.user_repository.create_user(user_data)
        return UserResponse.from_orm(user)
    
    def authenticate_user(self, login_data: UserLogin) -> Optional[UserResponse]:
        """Authenticate a user by email and password."""
        user = self.user_repository.get_user_by_email(login_data.email)
        if not user:
            return None
            
        if not self.user_repository.verify_password(user, login_data.password):
            return None
            
        return UserResponse.from_orm(user)
    
    def create_access_token(self, user_id: uuid.UUID) -> str:
        """Create JWT access token."""
        expire = datetime.now() + timedelta(minutes=self.token_expire_minutes)
        to_encode = {
            "sub": str(user_id),
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[uuid.UUID]:
        """Verify JWT token and return user ID if valid."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                return None
            return uuid.UUID(user_id)
        except jwt.PyJWTError:
            return None