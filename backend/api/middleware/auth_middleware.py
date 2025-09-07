from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
import logging

from core.services.auth_service import AuthService
from database.repositories.user_repository import UserRepository
from database.connections.rds_postgres import postgres_connection

logger = logging.getLogger(__name__)

class JWTBearerMiddleware(HTTPBearer):
    """JWT Authentication middleware for FastAPI"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.auto_error = auto_error
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Process the request to authenticate"""
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                logger.warning("Invalid authentication scheme")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme"
                )
            
            if not self.verify_jwt(request, credentials.credentials):
                logger.warning("Invalid or expired token")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired token"
                )
            
            return credentials.credentials
        
        if self.auto_error:
            logger.warning("Invalid authorization code")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code"
            )
        
        return None
    
    def verify_jwt(self, request: Request, token: str) -> bool:
        """Verify JWT token and attach user to request state"""
        try:
            # Get database session
            db = postgres_connection.SessionLocal()
            
            # Create user repository
            user_repository = UserRepository(db)
            
            # Create auth service
            auth_service = AuthService(user_repository)
            
            # Verify token
            user_id = auth_service.verify_token(token)
            if not user_id:
                return False
            
            # Get user from database
            user = user_repository.get_user_by_id(user_id)
            if not user:
                return False
            
            # Attach user to request state for later use
            request.state.user = user
            request.state.user_id = user_id
            
            return True
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return False
        finally:
            db.close()


def admin_required(request: Request):
    """Middleware function to check if user is an admin"""
    user = getattr(request.state, "user", None)
    if not user or not user.is_admin:
        logger.warning("Admin access required but user is not admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return True


def get_current_user_factory() -> Callable:
    """Factory function to create a dependency for getting the current user"""
    def get_current_user(request: Request):
        user = getattr(request.state, "user", None)
        if not user:
            logger.warning("Authenticated user required but not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Authentication required"
            )
        return user
    return get_current_user