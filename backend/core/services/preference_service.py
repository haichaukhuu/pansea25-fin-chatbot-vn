import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from database.repositories.preference_repository import PreferenceRepository
from database.repositories.user_repository import UserRepository
from database.connections.rds_postgres import postgres_connection
from database.models.preference_models import (
    UserPreference,
    PreferenceCreateRequest,
    PreferenceUpdateRequest
)
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class PreferenceService:
    """
    Service class for managing user preferences
    """
    
    def __init__(self):
        """Initialize the preference service."""
        self.preference_repository = PreferenceRepository()
    
    def _get_user_repository(self):
        """Get a UserRepository instance with database session."""
        db_session = postgres_connection.get_db_session()
        return UserRepository(db_session)
    
    def _validate_user_exists(self, user_id: str) -> Dict[str, str]:
        """
        Validate that user exists in RDS and return user data.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            Dict containing user_id_str and user_email
            
        Raises:
            ValueError: If user not found
        """
        with postgres_connection.get_db_session() as db_session:
            user_repository = UserRepository(db_session)
            # Convert string user_id to UUID for database query
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            user = user_repository.get_user_by_id(user_uuid)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            return {
                'user_id_str': str(user.id),
                'user_email': user.email
            }
    
    def create_user_preference(
        self, 
        user_id: str, 
        preference_data: PreferenceCreateRequest
    ) -> Dict[str, Any]:
        """
        Create new user preferences with business validation.
        
        Args:
            user_id: User ID to create preferences for
            preference_data: Preference data to create
            
        Returns:
            Dict with success status, message, and data
        """
        try:
            # Validate user exists
            user_data = self._validate_user_exists(user_id)
            
            # Check if preferences already exist
            if self.preference_repository.exists(user_id):
                existing_preference = self.preference_repository.get_by_user_id(user_id)
                return {
                    'success': False,
                    'message': 'User preferences already exist. Use update instead.',
                    'data': existing_preference
                }
            
            # Create UserPreference object
            current_time = datetime.utcnow().isoformat()
            user_preference = UserPreference(
                user_id=user_data['user_id_str'],
                user_email=user_data['user_email'],
                questionnaire_answer=preference_data.questionnaire_answer,
                recorded_on=current_time,
                updated_on=current_time
            )
            
            # Save via repository
            created_preference = self.preference_repository.create(user_preference)
            
            logger.info(f"Successfully created preferences for user {user_id}")
            
            return {
                'success': True,
                'message': 'User preferences created successfully',
                'data': created_preference
            }
            
        except ValueError as e:
            logger.error(f"Validation error creating preferences for user {user_id}: {e}")
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'PreferenceAlreadyExists':
                return {
                    'success': False,
                    'message': 'User preferences already exist',
                    'data': None
                }
            else:
                logger.error(f"Database error creating preferences for user {user_id}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error creating preferences for user {user_id}: {e}")
            raise
    
    def get_user_preference(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences by user ID.
        
        Args:
            user_id: User ID to get preferences for
            
        Returns:
            Dict with success status, message, and data
        """
        try:
            user_preference = self.preference_repository.get_by_user_id(user_id)
            
            if not user_preference:
                return {
                    'success': False,
                    'message': 'User preferences not found',
                    'data': None
                }
            
            return {
                'success': True,
                'message': 'User preferences retrieved successfully',
                'data': user_preference
            }
            
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'data': None
            }
    
    def update_user_preference(
        self, 
        user_id: str, 
        preference_data: PreferenceUpdateRequest
    ) -> Dict[str, Any]:
        """
        Update existing user preferences with business validation.
        If preferences don't exist, create them automatically.
        
        Args:
            user_id: User ID to update preferences for
            preference_data: Preference data to update
            
        Returns:
            Dict with success status, message, and data
        """
        try:
            # Check if preferences exist
            if not self.preference_repository.exists(user_id):
                logger.info(f"No preferences found for user {user_id}, creating new preferences")
                
                # Validate user exists before creating preferences
                user_data = self._validate_user_exists(user_id)
                
                # Create new preferences if user exists but has no preferences yet
                if preference_data.questionnaire_answer:
                    # Convert update request to create request
                    create_request = PreferenceCreateRequest(
                        questionnaire_answer=preference_data.questionnaire_answer
                    )
                    return self.create_user_preference(user_id, create_request)
                else:
                    return {
                        'success': False,
                        'message': 'No preference data provided for creation',
                        'data': None
                    }
            
            # Prepare update data
            update_data = {}
            if preference_data.questionnaire_answer:
                update_data['questionnaire_answer'] = preference_data.questionnaire_answer.dict(by_alias=True)
            
            # Update via repository
            updated_preference = self.preference_repository.update(user_id, update_data)
            
            logger.info(f"Successfully updated preferences for user {user_id}")
            
            return {
                'success': True,
                'message': 'User preferences updated successfully',
                'data': updated_preference
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'PreferenceNotFound':
                return {
                    'success': False,
                    'message': 'User preferences not found. Create preferences first.',
                    'data': None
                }
            else:
                logger.error(f"Database error updating preferences for user {user_id}: {e}")
                return {
                    'success': False,
                    'message': f'Error updating preferences: {str(e)}',
                    'data': None
                }
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'data': None
            }
    
    def delete_user_preference(self, user_id: str) -> Dict[str, Any]:
        """
        Delete user preferences.
        
        Args:
            user_id: User ID to delete preferences for
            
        Returns:
            Dict with success status and message
        """
        try:
            deleted = self.preference_repository.delete(user_id)
            
            if not deleted:
                return {
                    'success': False,
                    'message': 'User preferences not found',
                    'data': None
                }
            
            logger.info(f"Successfully deleted preferences for user {user_id}")
            
            return {
                'success': True,
                'message': 'User preferences deleted successfully',
                'data': None
            }
            
        except Exception as e:
            logger.error(f"Error deleting preferences for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'Error deleting preferences: {str(e)}',
                'data': None
            }
    
    def check_preference_exists(self, user_id: str) -> bool:
        """
        Check if user preferences exist.
        
        Args:
            user_id: User ID to check
            
        Returns:
            bool: True if preferences exist, False otherwise
        """
        return self.preference_repository.exists(user_id)
    
    def get_user_preference_by_email(self, email: str) -> Dict[str, Any]:
        """
        Get user preferences by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Dict with success status, message, and data
        """
        try:
            # First get user ID from RDS
            with postgres_connection.get_db_session() as db_session:
                user_repository = UserRepository(db_session)
                user = user_repository.get_user_by_email(email)
                if not user:
                    return {
                        'success': False,
                        'message': 'User not found',
                        'data': None
                    }
            
            # Then get preferences using user ID
            return self.get_user_preference(str(user.id))
            
        except Exception as e:
            logger.error(f"Error getting preferences by email {email}: {e}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'data': None
            }
    
    def upsert_user_preference(
        self, 
        user_id: str, 
        preference_data: PreferenceCreateRequest
    ) -> Dict[str, Any]:
        """
        Create or update user preferences (upsert operation).
        
        Args:
            user_id: User ID to upsert preferences for
            preference_data: Preference data to upsert
            
        Returns:
            Dict with success status, message, and data
        """
        try:
            # Check if preferences exist
            exists = self.preference_repository.exists(user_id)
            
            if exists:
                # Update existing preferences
                update_request = PreferenceUpdateRequest(
                    questionnaire_answer=preference_data.questionnaire_answer
                )
                return self.update_user_preference(user_id, update_request)
            else:
                # Create new preferences
                return self.create_user_preference(user_id, preference_data)
                
        except Exception as e:
            logger.error(f"Error upserting preferences for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'data': None
            }


# Global service instance
preference_service = PreferenceService()