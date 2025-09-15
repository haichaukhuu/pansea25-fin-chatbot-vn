import logging
import uuid
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError

from database.connections.dynamodb_chat_history import DynamoDBChatHistoryConnection
from database.models.chat_history_item import ChatHistoryItem

logger = logging.getLogger(__name__)

class ChatHistoryRepository:
    """Repository for managing chat history data in DynamoDB."""
    
    def __init__(self):
        """Initialize with DynamoDB connection."""
        conn = DynamoDBChatHistoryConnection.get_instance()
        self.client = conn.get_client()
        self.table_name = conn.get_table_name()
    
    def save_message(self, chat_item: ChatHistoryItem) -> bool:
        """
        Save a message to the chat history.
        
        Args:
            chat_item: The ChatHistoryItem to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.client.put_item(
                TableName=self.table_name,
                Item=chat_item.to_dynamodb_item()
            )
            logger.info(f"Saved message to chat history: {chat_item.conversation_id}")
            return True
        except ClientError as e:
            logger.error(f"Error saving chat history: {str(e)}")
            return False
    
    def get_conversation(self, user_id: str, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a specific conversation.
        
        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            
        Returns:
            List of chat messages
        """
        try:
            response = self.client.query(
                TableName=self.table_name,
                KeyConditionExpression="user_id = :uid",
                FilterExpression="conversation_id = :cid",
                ExpressionAttributeValues={
                    ":uid": {"S": user_id},
                    ":cid": {"S": conversation_id}
                }
            )
            
            # Extract and format the items
            messages = []
            for item in response.get('Items', []):
                messages.append(self._dynamodb_to_dict(item))
                
            # Sort by timestamp
            messages.sort(key=lambda x: x['timestamp'])
            
            return messages
        except ClientError as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []
    
    def get_user_conversations(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a list of user's conversations (most recent first).
        
        Args:
            user_id: The user ID
            limit: Maximum number of conversations to retrieve
            offset: Number of conversations to skip (for pagination)
            
        Returns:
            List of conversation summaries
        """
        try:
            response = self.client.query(
                TableName=self.table_name,
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={
                    ":uid": {"S": user_id}
                },
                ScanIndexForward=False  # Get most recent first
            )
            
            # Process results to group by conversation and get the most recent message per conversation
            conversations = {}
            for item in response.get('Items', []):
                item_dict = self._dynamodb_to_dict(item)
                conv_id = item_dict['conversation_id']
                
                if conv_id not in conversations:
                    conversations[conv_id] = {
                        'conversation_id': conv_id,
                        'last_message': item_dict['content'],
                        'last_updated': item_dict['created_at'],
                        'message_count': 1,
                        'last_timestamp': item_dict['timestamp']  # Keep track of the most recent timestamp
                    }
                else:
                    conversations[conv_id]['message_count'] += 1
                    # Update last_message and last_updated if this message is more recent
                    if item_dict['timestamp'] > conversations[conv_id]['last_timestamp']:
                        conversations[conv_id]['last_message'] = item_dict['content']
                        conversations[conv_id]['last_updated'] = item_dict['created_at']
                        conversations[conv_id]['last_timestamp'] = item_dict['timestamp']
            
            # Sort conversations by last_timestamp (most recent first) and apply pagination
            sorted_conversations = sorted(
                conversations.values(), 
                key=lambda x: x['last_timestamp'], 
                reverse=True
            )
            
            # Apply offset and limit at the conversation level
            start_idx = offset
            end_idx = offset + limit
            paginated_conversations = sorted_conversations[start_idx:end_idx]
            
            # Remove the helper timestamp field before returning
            for conv in paginated_conversations:
                del conv['last_timestamp']
            
            return paginated_conversations
        except ClientError as e:
            logger.error(f"Error retrieving user conversations: {str(e)}")
            return []
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Delete an entire conversation.
        
        Args:
            user_id: The user ID
            conversation_id: The conversation ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First, retrieve all messages in the conversation
            messages = self.get_conversation(user_id, conversation_id)
            
            # Delete each message
            for message in messages:
                self.client.delete_item(
                    TableName=self.table_name,
                    Key={
                        'user_id': {'S': user_id},
                        'timestamp': {'N': str(message['timestamp'])}
                    }
                )
            
            logger.info(f"Deleted conversation {conversation_id} for user {user_id}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            return False
    
    def _dynamodb_to_dict(self, item: Dict) -> Dict[str, Any]:
        """Convert DynamoDB item to a Python dictionary."""
        result = {}
        
        for key, value in item.items():
            if 'S' in value:
                result[key] = value['S']
            elif 'N' in value:
                result[key] = int(value['N']) if '.' not in value['N'] else float(value['N'])
            elif 'BOOL' in value:
                result[key] = value['BOOL']
            elif 'L' in value:
                result[key] = [self._dynamodb_to_dict(item) for item in value['L']]
            elif 'M' in value:
                result[key] = self._dynamodb_to_dict(value['M'])
            # Add more type conversions as needed
        
        return result