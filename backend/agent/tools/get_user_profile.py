"""
User Profile Tool for ReAct Agent
This tool retrieves user preferences from DynamoDB
"""

from typing import Dict, Any, Optional, List, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import logging
from database.connections.dynamodb_preference import get_preference_table

logger = logging.getLogger(__name__)

class UserProfileInput(BaseModel):
    """Input for UserProfileTool"""
    user_id: str = Field(..., description="The ID of the user to retrieve preferences for")
    preference_keys: Optional[List[str]] = Field(
        None, 
        description="Optional list of specific preference keys to retrieve. If not provided, all preferences will be returned."
    )

class GetUserProfileTool(BaseTool):
    """Tool for retrieving user preferences from DynamoDB"""
    name = "get_user_profile"
    description = """
    Use this tool to retrieve user preferences and profile information.
    This is useful when you need to personalize responses based on user preferences,
    such as preferred language, financial interests, agricultural focus areas, etc.
    
    Input should be a user_id and optionally specific preference keys to retrieve.
    """
    args_schema: Type[BaseModel] = UserProfileInput
    return_direct = False
    
    def _run(self, user_id: str, preference_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the tool to get user preferences"""
        try:
            logger.info(f"Retrieving user profile for user_id: {user_id}")
            
            # Get the preference table
            table = get_preference_table()
            
            # Query the table for the user's preferences
            response = table.get_item(
                Key={
                    'user_id': user_id
                }
            )
            
            # Check if the item exists
            if 'Item' not in response:
                logger.warning(f"No preferences found for user_id: {user_id}")
                return {"user_id": user_id, "preferences": {}, "message": "No preferences found for this user"}
            
            # Extract preferences
            preferences = response['Item'].get('preferences', {})
            
            # Filter preferences if specific keys were requested
            if preference_keys:
                filtered_preferences = {k: preferences.get(k) for k in preference_keys if k in preferences}
                result = {
                    "user_id": user_id,
                    "preferences": filtered_preferences,
                    "requested_keys": preference_keys
                }
            else:
                result = {
                    "user_id": user_id,
                    "preferences": preferences
                }
            
            logger.info(f"Successfully retrieved preferences for user_id: {user_id}")
            return result
            
        except Exception as e:
            error_msg = f"Error retrieving user profile: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "user_id": user_id}
    
    async def _arun(self, user_id: str, preference_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Async implementation of the tool"""
        # For DynamoDB operations, we can use the synchronous version
        return self._run(user_id=user_id, preference_keys=preference_keys)