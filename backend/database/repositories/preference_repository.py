import logging
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

from database.connections.dynamodb_preference import get_dynamodb_table
from database.models.preference_models import (
    UserPreference,
    convert_to_dynamodb_item,
    convert_from_dynamodb_item
)

logger = logging.getLogger(__name__)


class PreferenceRepository:
    """
    Repository class for preference storage operations.
    Handles pure CRUD operations without business logic.
    """
    
    def __init__(self):
        """Initialize the preference repository."""
        self.table = None
    
    def _get_table(self):
        """Get DynamoDB table connection."""
        if not self.table:
            self.table = get_dynamodb_table()
        return self.table
    
    def create(self, user_preference: UserPreference) -> UserPreference:
        """
        Create a new user preference record in DynamoDB.
        
        Args:
            user_preference: UserPreference object to create
            
        Returns:
            UserPreference: The created preference object
            
        Raises:
            ClientError: If preference already exists (ConditionalCheckFailedException)
            Exception: For other database errors
        """
        try:
            # Convert to DynamoDB item format
            item = convert_to_dynamodb_item(user_preference)
            
            # Save to DynamoDB with condition to prevent overwrite
            table = self._get_table()
            table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(user_id)'
            )
            
            logger.info(f"Successfully created preferences for user {user_preference.user_id}")
            return user_preference
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConditionalCheckFailedException':
                logger.warning(f"Preferences already exist for user {user_preference.user_id}")
                raise ClientError(
                    error_response={'Error': {'Code': 'PreferenceAlreadyExists'}},
                    operation_name='put_item'
                )
            else:
                logger.error(f"DynamoDB error creating preferences for user {user_preference.user_id}: {e}")
                raise
    
    def get_by_user_id(self, user_id: str) -> Optional[UserPreference]:
        """
        Get user preferences by user ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            UserPreference object if found, None otherwise
            
        Raises:
            Exception: For database errors
        """
        try:
            table = self._get_table()
            
            response = table.get_item(
                Key={'user_id': user_id}
            )
            
            if 'Item' not in response:
                logger.info(f"No preferences found for user {user_id}")
                return None
            
            # Convert DynamoDB item to UserPreference model
            user_preference = convert_from_dynamodb_item(response['Item'])
            
            logger.info(f"Successfully retrieved preferences for user {user_id}")
            return user_preference
            
        except ClientError as e:
            logger.error(f"DynamoDB error getting preferences for user {user_id}: {e}")
            raise
    
    def update(self, user_id: str, update_data: Dict[str, Any]) -> UserPreference:
        """
        Update existing user preferences in DynamoDB.
        
        Args:
            user_id: User ID to update
            update_data: Dictionary of fields to update
            
        Returns:
            UserPreference: Updated preference object
            
        Raises:
            ClientError: If preference doesn't exist
            Exception: For other database errors
        """
        try:
            table = self._get_table()
            current_time = datetime.utcnow().isoformat()
            
            # Prepare update expression
            update_expression = "SET updated_on = :updated_on"
            expression_attribute_values = {
                ':updated_on': current_time
            }
            
            # Add other fields to update
            for key, value in update_data.items():
                if key != 'updated_on':  # Skip updated_on as we set it automatically
                    update_expression += f", {key} = :{key}"
                    expression_attribute_values[f':{key}'] = value
            
            # Update the item
            response = table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW',
                ConditionExpression='attribute_exists(user_id)'  # Ensure item exists
            )
            
            # Convert updated item to UserPreference model
            updated_preference = convert_from_dynamodb_item(response['Attributes'])
            
            logger.info(f"Successfully updated preferences for user {user_id}")
            return updated_preference
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConditionalCheckFailedException':
                logger.warning(f"Preferences not found for user {user_id}")
                raise ClientError(
                    error_response={'Error': {'Code': 'PreferenceNotFound'}},
                    operation_name='update_item'
                )
            else:
                logger.error(f"DynamoDB error updating preferences for user {user_id}: {e}")
                raise
    
    def delete(self, user_id: str) -> bool:
        """
        Delete user preferences from DynamoDB.
        
        Args:
            user_id: User ID to delete preferences for
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            Exception: For database errors
        """
        try:
            table = self._get_table()
            
            # Delete the item
            response = table.delete_item(
                Key={'user_id': user_id},
                ReturnValues='ALL_OLD'
            )
            
            if 'Attributes' not in response:
                logger.info(f"No preferences found to delete for user {user_id}")
                return False
            
            logger.info(f"Successfully deleted preferences for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"DynamoDB error deleting preferences for user {user_id}: {e}")
            raise
    
    def exists(self, user_id: str) -> bool:
        """
        Check if user preferences exist in DynamoDB.
        
        Args:
            user_id: User ID to check
            
        Returns:
            bool: True if preferences exist, False otherwise
        """
        try:
            table = self._get_table()
            
            response = table.get_item(
                Key={'user_id': user_id},
                ProjectionExpression='user_id'  # Only get the key to check existence
            )
            
            return 'Item' in response
            
        except Exception as e:
            logger.error(f"Error checking preference existence for user {user_id}: {e}")
            return False