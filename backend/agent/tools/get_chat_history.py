"""
Chat History Tool for ReAct Agent
This tool retrieves chat history from DynamoDB
"""

from typing import Dict, Any, Optional, List, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import logging
from database.connections.dynamodb_chat_history import DynamoDBChatHistoryConnection

logger = logging.getLogger(__name__)

class ChatHistoryInput(BaseModel):
    """Input for ChatHistoryTool"""
    user_id: str = Field(..., description="The ID of the user to retrieve chat history for")
    conversation_id: Optional[str] = Field(
        None, 
        description="Optional conversation ID to filter history. If not provided, recent messages across all conversations will be returned."
    )
    limit: Optional[int] = Field(
        10, 
        description="Maximum number of messages to retrieve"
    )

class GetChatHistoryTool(BaseTool):
    """Tool for retrieving chat history from DynamoDB"""
    name = "get_chat_history"
    description = """
    Use this tool to retrieve previous chat messages between the user and the assistant.
    This is useful for maintaining context in conversations and understanding the user's previous questions.
    
    Input should be a user_id and optionally a specific conversation_id.
    """
    args_schema: Type[BaseModel] = ChatHistoryInput
    return_direct = False
    
    def _run(self, user_id: str, conversation_id: Optional[str] = None, limit: Optional[int] = 10) -> Dict[str, Any]:
        """Run the tool to get chat history"""
        try:
            logger.info(f"Retrieving chat history for user_id: {user_id}, conversation_id: {conversation_id}")
            
            # Get the DynamoDB connection
            dynamo_connection = DynamoDBChatHistoryConnection.get_instance()
            client = dynamo_connection.get_client()
            table_name = dynamo_connection.get_table_name()
            
            # Prepare query parameters
            if conversation_id:
                # Query for specific conversation
                query_params = {
                    'TableName': table_name,
                    'KeyConditionExpression': 'user_id = :uid AND conversation_id = :cid',
                    'ExpressionAttributeValues': {
                        ':uid': {'S': user_id},
                        ':cid': {'S': conversation_id}
                    },
                    'ScanIndexForward': False,  # Sort in descending order (newest first)
                    'Limit': limit
                }
            else:
                # Query for recent messages across all conversations
                query_params = {
                    'TableName': table_name,
                    'KeyConditionExpression': 'user_id = :uid',
                    'ExpressionAttributeValues': {
                        ':uid': {'S': user_id}
                    },
                    'ScanIndexForward': False,  # Sort in descending order (newest first)
                    'Limit': limit
                }
            
            # Execute the query
            response = client.query(**query_params)
            
            # Process the results
            messages = []
            for item in response.get('Items', []):
                message = {
                    'user_id': item.get('user_id', {}).get('S', ''),
                    'conversation_id': item.get('conversation_id', {}).get('S', ''),
                    'timestamp': int(item.get('timestamp', {}).get('N', 0)),
                    'message_type': item.get('message_type', {}).get('S', ''),
                    'content': item.get('content', {}).get('S', ''),
                    'created_at': item.get('created_at', {}).get('S', '')
                }
                
                # Add sources if available
                if 'sources' in item:
                    try:
                        sources_str = item['sources'].get('S', '[]')
                        message['sources'] = eval(sources_str)  # Convert string to list
                    except:
                        message['sources'] = []
                
                # Add tools if available
                if 'tools' in item:
                    try:
                        tools_str = item['tools'].get('S', '[]')
                        message['tools'] = eval(tools_str)  # Convert string to list
                    except:
                        message['tools'] = []
                
                messages.append(message)
            
            result = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "messages": messages,
                "count": len(messages)
            }
            
            logger.info(f"Successfully retrieved {len(messages)} chat history messages")
            return result
            
        except Exception as e:
            error_msg = f"Error retrieving chat history: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "user_id": user_id, "conversation_id": conversation_id}
    
    async def _arun(self, user_id: str, conversation_id: Optional[str] = None, limit: Optional[int] = 10) -> Dict[str, Any]:
        """Async implementation of the tool"""
        # For DynamoDB operations, we can use the synchronous version
        return self._run(user_id=user_id, conversation_id=conversation_id, limit=limit)