import logging
import uuid
from typing import List, Dict, Any, Optional

from database.repositories.chat_history_repository import ChatHistoryRepository
from database.models.chat_history_item import ChatHistoryItem

logger = logging.getLogger(__name__)

class ChatHistoryService:
    """Service for managing chat history."""
    
    def __init__(self):
        """Initialize with chat history repository."""
        self.repository = ChatHistoryRepository()
    
    def save_user_message(self, user_id: str, message_content: str, 
                         conversation_id: Optional[str] = None) -> str:
        """
        Save a user message to the chat history.
        
        Args:
            user_id: The user ID
            message_content: The user's message content
            conversation_id: Optional conversation ID (if continuing a conversation)
            
        Returns:
            str: The conversation ID
        """
        chat_item = ChatHistoryItem.create_user_message(
            user_id=user_id,
            content=message_content,
            conversation_id=conversation_id
        )
        
        success = self.repository.save_message(chat_item)
        if not success:
            logger.error(f"Failed to save user message for user {user_id}")
        
        return chat_item.conversation_id
    
    def save_assistant_message(self, user_id: str, message_content: str,
                             conversation_id: str, sources: Optional[List] = None,
                             tools: Optional[List] = None) -> bool:
        """
        Save an assistant message to the chat history.
        
        Args:
            user_id: The user ID
            message_content: The assistant's message content
            conversation_id: The conversation ID
            sources: Optional list of sources
            tools: Optional list of tools used
            
        Returns:
            bool: True if successful
        """
        chat_item = ChatHistoryItem.create_assistant_message(
            user_id=user_id,
            content=message_content,
            conversation_id=conversation_id,
            sources=sources,
            tools=tools
        )
        
        return self.repository.save_message(chat_item)
    
    def get_conversation_history(self, user_id: str, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve the full history of a conversation.
        
        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            
        Returns:
            List of messages in the conversation
        """
        return self.repository.get_conversation(user_id, conversation_id)
    
    def get_user_conversations(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a summary of user's recent conversations.
        
        Args:
            user_id: The user ID
            limit: Maximum number of conversations to retrieve
            offset: Number of conversations to skip (for pagination)
            
        Returns:
            List of conversation summaries
        """
        return self.repository.get_user_conversations(user_id, limit, offset)
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Delete an entire conversation.
        
        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            
        Returns:
            bool: True if successful
        """
        return self.repository.delete_conversation(user_id, conversation_id)