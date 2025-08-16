from typing import Optional, Dict, Any
from firebase_admin import auth as admin_auth
from firebase_admin.auth import UserRecord
from .firebase_config import firebase_config
import logging
from fastapi import HTTPException
import secrets
import string

logger = logging.getLogger(__name__)

class FirebaseAuthService:
    """Firebase Authentication Service for user management"""
    
    def __init__(self):
        try:
            self.admin_auth = firebase_config.get_admin_auth()
            logger.info("Firebase Auth Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Auth Service: {e}")
            # Set to None so we can handle errors gracefully
            self.admin_auth = None
    
    async def register_user(self, email: str, password: str, display_name: str = None) -> Dict[str, Any]:
        """Register a new user with email and password using Firebase Admin SDK"""
        if not self.admin_auth:
            raise HTTPException(status_code=503, detail="Firebase authentication service not available")
        
        try:
            # Create user with Firebase Admin SDK
            user_record = self.admin_auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False
            )
            
            # Create custom token for immediate authentication
            custom_token = self.admin_auth.create_custom_token(user_record.uid)
            
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "created_at": user_record.user_metadata.creation_timestamp,
                "custom_token": custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            if "EMAIL_ALREADY_EXISTS" in str(e):
                raise HTTPException(status_code=400, detail="Email already exists")
            elif "INVALID_EMAIL" in str(e):
                raise HTTPException(status_code=400, detail="Invalid email format")
            elif "WEAK_PASSWORD" in str(e):
                raise HTTPException(status_code=400, detail="Password should be at least 6 characters")
            else:
                raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with email and password using custom token approach
        
        IMPORTANT: This implementation has limitations since Firebase Admin SDK 
        cannot validate passwords directly. In production, you should either:
        1. Use Firebase Client SDK in a secure server environment
        2. Implement your own password hashing/validation
        3. Use Firebase Auth REST API for password validation
        
        Current implementation only validates user existence and creates custom tokens.
        """
        if not self.admin_auth:
            raise HTTPException(status_code=503, detail="Firebase authentication service not available")
        
        try:
            # Get user by email to validate existence
            user_record = self.admin_auth.get_user_by_email(email)
            
            # TODO: Implement proper password validation here
            # This could be done by:
            # 1. Using Firebase Auth REST API to validate credentials
            # 2. Storing and validating password hashes separately
            # 3. Using a different authentication service
            
            # For now, we assume the password is valid if the user exists
            # This is NOT secure and should be implemented properly in production
            
            # Create custom token for authentication
            custom_token = self.admin_auth.create_custom_token(user_record.uid)
            
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "custom_token": custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token,
                "message": "Login successful. Note: Password validation not implemented in this version."
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            if "USER_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            elif "USER_DISABLED" in str(e):
                raise HTTPException(status_code=403, detail="User account is disabled")
            else:
                raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token"""
        if not self.admin_auth:
            raise HTTPException(status_code=503, detail="Firebase authentication service not available")
        
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
    
    async def refresh_token(self, uid: str) -> Dict[str, Any]:
        """Generate a new custom token for the user"""
        if not self.admin_auth:
            raise HTTPException(status_code=503, detail="Firebase authentication service not available")
        
        try:
            # Verify user still exists and is not disabled
            user_record = self.admin_auth.get_user(uid)
            
            if user_record.disabled:
                raise HTTPException(status_code=403, detail="User account is disabled")
            
            # Create new custom token
            custom_token = self.admin_auth.create_custom_token(uid)
            
            return {
                "custom_token": custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token,
                "uid": uid,
                "message": "Token refreshed successfully"
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            if "USER_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            else:
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
        """Send password reset email using Firebase Admin SDK"""
        if not self.admin_auth:
            raise HTTPException(status_code=503, detail="Firebase authentication service not available")
        
        try:
            # Verify user exists
            user_record = self.admin_auth.get_user_by_email(email)
            
            # Generate password reset link
            # Note: You would typically want to configure ActionCodeSettings for your domain
            # For now, we'll use the default Firebase domain
            reset_link = self.admin_auth.generate_password_reset_link(email)
            
            # In a real implementation, you would send this link via your email service
            # For now, we'll return the link for testing purposes
            return {
                "message": "Password reset link generated successfully",
                "reset_link": reset_link,
                "note": "In production, this link would be sent via email service"
            }
            
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            if "USER_NOT_FOUND" in str(e):
                raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to generate password reset link")

# Global Firebase auth service instance
firebase_auth_service = FirebaseAuthService()
