import logging
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

from database.connections.dynamodb_connection import get_dynamodb_table
from database.models.dynamodb_models import (
    UserPreference, 
    QuestionnaireAnswer,
    PreferenceCreateRequest,
    PreferenceUpdateRequest,
    convert_to_dynamodb_item,
    convert_from_dynamodb_item
)
from database.repositories.user_repository import UserRepository
from database.connections.rds_postgres import postgres_connection

logger = logging.getLogger(__name__)


class DynamoDBService:
    """
    Service class for managing user preferences in DynamoDB.
    """
    
    def __init__(self):
        """Initialize the DynamoDB service."""
        pass
    
    def _get_user_repository(self):
        """Get a UserRepository instance with database session."""
        db_session = postgres_connection.get_db_session()
        return UserRepository(db_session)
    
    def create_user_preference(
        self, 
        user_id: str, 
        preference_data: PreferenceCreateRequest
    ) -> Dict[str, Any]:
        """
        Create new user preferences in DynamoDB.
        """
        try:
            # Get user information from RDS
            with postgres_connection.get_db_session() as db_session:
                user_repository = UserRepository(db_session)
                # Convert string user_id to UUID for database query
                import uuid
                user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
                user = user_repository.get_user_by_id(user_uuid)
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Extract user data while session is active
                user_id_str = str(user.id)
                user_email = user.email
            
            # Check if preferences already exist
            existing_preference = self.get_user_preference(user_id)
            if existing_preference.get('success') and existing_preference.get('data'):
                return {
                    'success': False,
                    'message': 'User preferences already exist. Use update instead.',
                    'data': existing_preference.get('data')
                }
            
            # Create UserPreference object
            current_time = datetime.utcnow().isoformat()
            user_preference = UserPreference(
                user_id=user_id_str,
                user_email=user_email,
                questionnaire_answer=preference_data.questionnaire_answer,
                recorded_on=current_time,
                updated_on=current_time
            )
            
            # Convert to DynamoDB item format
            item = convert_to_dynamodb_item(user_preference)
            
            # Save to DynamoDB
            table = get_dynamodb_table()
            table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(user_id)'
            )
            
            logger.info(f"Successfully created preferences for user {user_id}")
            
            return {
                'success': True,
                'message': 'User preferences created successfully',
                'data': user_preference
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConditionalCheckFailedException':
                logger.warning(f"Preferences already exist for user {user_id}")
                return {
                    'success': False,
                    'message': 'User preferences already exist',
                    'data': None
                }
            else:
                logger.error(f"DynamoDB error creating preferences for user {user_id}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error creating preferences for user {user_id}: {e}")
            raise
    
    def get_user_preference(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences from DynamoDB.
        """
        try:
            table = get_dynamodb_table()
            
            response = table.get_item(
                Key={'user_id': user_id}
            )
            
            if 'Item' not in response:
                logger.info(f"No preferences found for user {user_id}")
                return {
                    'success': False,
                    'message': 'User preferences not found',
                    'data': None
                }
            
            # Convert DynamoDB item to UserPreference model
            user_preference = convert_from_dynamodb_item(response['Item'])
            
            logger.info(f"Successfully retrieved preferences for user {user_id}")
            
            return {
                'success': True,
                'message': 'User preferences retrieved successfully',
                'data': user_preference
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error getting preferences for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'Error retrieving preferences: {str(e)}',
                'data': None
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
        Update existing user preferences in DynamoDB.
        """
        try:
            # Check if preferences exist
            existing_response = self.get_user_preference(user_id)
            if not existing_response.get('success'):
                return {
                    'success': False,
                    'message': 'User preferences not found. Create preferences first.',
                    'data': None
                }
            
            table = get_dynamodb_table()
            current_time = datetime.utcnow().isoformat()
            
            # Prepare update expression
            update_expression = "SET updated_on = :updated_on"
            expression_attribute_values = {
                ':updated_on': current_time
            }
            
            # Update questionnaire answers if provided
            if preference_data.questionnaire_answer:
                update_expression += ", questionnaire_answer = :questionnaire_answer"
                expression_attribute_values[':questionnaire_answer'] = \
                    preference_data.questionnaire_answer.dict(by_alias=True)
            
            # Update the item
            response = table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            
            # Convert updated item to UserPreference model
            updated_preference = convert_from_dynamodb_item(response['Attributes'])
            
            logger.info(f"Successfully updated preferences for user {user_id}")
            
            return {
                'success': True,
                'message': 'User preferences updated successfully',
                'data': updated_preference
            }
            
        except ClientError as e:
            logger.error(f"DynamoDB error updating preferences for user {user_id}: {e}")
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
        Delete user preferences from DynamoDB.
        """
        try:
            table = get_dynamodb_table()
            
            # Delete the item
            response = table.delete_item(
                Key={'user_id': user_id},
                ReturnValues='ALL_OLD'
            )
            
            if 'Attributes' not in response:
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
            
        except ClientError as e:
            logger.error(f"DynamoDB error deleting preferences for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'Error deleting preferences: {str(e)}',
                'data': None
            }
        except Exception as e:
            logger.error(f"Error deleting preferences for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'data': None
            }
    
    def check_preference_exists(self, user_id: str) -> bool:
        """
        Check user preferences exist in DynamoDB.
        """
        try:
            table = get_dynamodb_table()
            
            response = table.get_item(
                Key={'user_id': user_id},
                ProjectionExpression='user_id'  # Only get the key to check existence
            )
            
            return 'Item' in response
            
        except Exception as e:
            logger.error(f"Error checking preference existence for user {user_id}: {e}")
            return False
    
    def get_user_preference_by_email(self, email: str) -> Dict[str, Any]:
        """
        Get user preferences by email address.
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
            
            # Then get preferences from DynamoDB
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
        """
        try:
            # Check if preferences exist
            exists = self.check_preference_exists(user_id)
            
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
dynamodb_service = DynamoDBService()
