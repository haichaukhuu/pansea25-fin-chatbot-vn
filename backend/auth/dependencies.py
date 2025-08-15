from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from .firebase_auth_service import firebase_auth_service
import logging

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from Firebase ID token
    """
    try:
        # Verify the token and get user info
        user_info = await firebase_auth_service.verify_id_token(credentials.credentials)
        return user_info
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current user if token is provided, otherwise return None
    """
    if not credentials:
        return None
    
    try:
        user_info = await firebase_auth_service.verify_id_token(credentials.credentials)
        return user_info
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None

async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to require admin role
    """
    custom_claims = current_user.get('firebase', {}).get('custom_claims', {})
    if not custom_claims.get('admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def require_verified_email(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to require email verification
    """
    if not current_user.get('email_verified', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user

def require_custom_claim(claim_name: str, claim_value: Any = True):
    """
    Factory function to create dependency that requires specific custom claim
    """
    async def _require_custom_claim(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        custom_claims = current_user.get('firebase', {}).get('custom_claims', {})
        if custom_claims.get(claim_name) != claim_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required custom claim '{claim_name}' not satisfied"
            )
        return current_user
    
    return _require_custom_claim
