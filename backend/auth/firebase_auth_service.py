from typing import Optional, Dict, Any
from firebase_admin import auth as admin_auth
from firebase_admin.auth import UserRecord
from .firebase_config import firebase_config
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class FirebaseAuthService:
    """Firebase Authentication Service for user management"""
    
    def __init__(self):
        self.admin_auth = firebase_config.get_admin_auth()
        self.client_auth = firebase_config.get_client_auth()
    
    async def register_user(self, email: str, password: str, display_name: str = None) -> Dict[str, Any]:
        """Register a new user with email and password"""
        try:
            # Create user with Firebase Client SDK (for password authentication)
            user_data = self.client_auth.create_user_with_email_and_password(email, password)
            
            # Update user profile if display_name is provided
            if display_name:
                user_record = self.admin_auth.update_user(
                    user_data['localId'],
                    display_name=display_name
                )
            else:
                user_record = self.admin_auth.get_user(user_data['localId'])
            
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "created_at": user_record.user_metadata.creation_timestamp,
                "last_sign_in": user_record.user_metadata.last_sign_in_timestamp
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            if "EMAIL_EXISTS" in str(e):
                raise HTTPException(status_code=400, detail="Email already exists")
            elif "WEAK_PASSWORD" in str(e):
                raise HTTPException(status_code=400, detail="Password should be at least 6 characters")
            elif "INVALID_EMAIL" in str(e):
                raise HTTPException(status_code=400, detail="Invalid email format")
            else:
                raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with email and password"""
        try:
            # Sign in with Firebase Client SDK
            user_data = self.client_auth.sign_in_with_email_and_password(email, password)
            
            # Get additional user info from Admin SDK
            user_record = self.admin_auth.get_user(user_data['localId'])
            
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "id_token": user_data['idToken'],
                "refresh_token": user_data['refreshToken'],
                "expires_in": user_data['expiresIn']
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            if "INVALID_LOGIN_CREDENTIALS" in str(e) or "INVALID_PASSWORD" in str(e):
                raise HTTPException(status_code=401, detail="Invalid email or password")
            elif "EMAIL_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            elif "USER_DISABLED" in str(e):
                raise HTTPException(status_code=403, detail="User account is disabled")
            else:
                raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token"""
        try:
            # Remove 'Bearer ' prefix if present
            if id_token.startswith('Bearer '):
                id_token = id_token[7:]
            
            # Verify the ID token
            decoded_token = self.admin_auth.verify_id_token(id_token)
            
            # Get user record for additional info
            user_record = self.admin_auth.get_user(decoded_token['uid'])
            
            return {
                "uid": decoded_token['uid'],
                "email": decoded_token.get('email'),
                "email_verified": decoded_token.get('email_verified', False),
                "display_name": user_record.display_name,
                "auth_time": decoded_token.get('auth_time'),
                "iat": decoded_token.get('iat'),
                "exp": decoded_token.get('exp'),
                "firebase": decoded_token.get('firebase', {})
            }
            
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            if "expired" in str(e).lower():
                raise HTTPException(status_code=401, detail="Token has expired")
            elif "invalid" in str(e).lower():
                raise HTTPException(status_code=401, detail="Invalid token")
            else:
                raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh user's ID token"""
        try:
            # Refresh the token using client SDK
            user_data = self.client_auth.refresh(refresh_token)
            
            return {
                "id_token": user_data['idToken'],
                "refresh_token": user_data['refreshToken'],
                "expires_in": user_data['expiresIn'],
                "uid": user_data['userId']
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(status_code=401, detail="Failed to refresh token")
    
    async def get_user_by_uid(self, uid: str) -> Dict[str, Any]:
        """Get user information by UID"""
        try:
            user_record = self.admin_auth.get_user(uid)
            
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "phone_number": user_record.phone_number,
                "photo_url": user_record.photo_url,
                "disabled": user_record.disabled,
                "created_at": user_record.user_metadata.creation_timestamp,
                "last_sign_in": user_record.user_metadata.last_sign_in_timestamp,
                "custom_claims": user_record.custom_claims or {}
            }
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            if "USER_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to get user information")
    
    async def update_user(self, uid: str, **kwargs) -> Dict[str, Any]:
        """Update user information"""
        try:
            user_record = self.admin_auth.update_user(uid, **kwargs)
            
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "phone_number": user_record.phone_number,
                "photo_url": user_record.photo_url,
                "disabled": user_record.disabled
            }
            
        except Exception as e:
            logger.error(f"Update user error: {e}")
            if "USER_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to update user")
    
    async def delete_user(self, uid: str) -> Dict[str, str]:
        """Delete user account"""
        try:
            self.admin_auth.delete_user(uid)
            return {"message": "User deleted successfully"}
            
        except Exception as e:
            logger.error(f"Delete user error: {e}")
            if "USER_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to delete user")
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> Dict[str, str]:
        """Set custom claims for a user"""
        try:
            self.admin_auth.set_custom_user_claims(uid, claims)
            return {"message": "Custom claims set successfully"}
            
        except Exception as e:
            logger.error(f"Set custom claims error: {e}")
            if "USER_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to set custom claims")
    
    async def send_password_reset_email(self, email: str) -> Dict[str, str]:
        """Send password reset email"""
        try:
            self.client_auth.send_password_reset_email(email)
            return {"message": "Password reset email sent successfully"}
            
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            if "EMAIL_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to send password reset email")

# Global Firebase auth service instance
firebase_auth_service = FirebaseAuthService()
