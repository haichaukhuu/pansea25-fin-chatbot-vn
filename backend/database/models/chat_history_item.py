import uuid
from datetime import datetime
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    """Model representing a chat history item in DynamoDB."""
    user_id: str
    timestamp: int  # Unix timestamp as sort key
    conversation_id: str
    message_type: str  # "user" or "assistant"
    content: str
    sources: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    tools: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    created_at: str  # ISO timestamp for display

    @classmethod
    def create_user_message(cls, user_id: str, content: str, conversation_id: Optional[str] = None):
        """Create a new user message entry."""
        now = datetime.now()
        return cls(
            user_id=user_id,
            timestamp=int(now.timestamp() * 1000),  # Convert to milliseconds
            conversation_id=conversation_id or str(uuid.uuid4()),
            message_type="user",
            content=content,
            created_at=now.isoformat()
        )
    
    @classmethod
    def create_assistant_message(cls, user_id: str, content: str, conversation_id: str, 
                               sources: Optional[List] = None, tools: Optional[List] = None):
        """Create a new assistant message entry."""
        now = datetime.now()
        return cls(
            user_id=user_id,
            timestamp=int(now.timestamp() * 1000),  # Convert to milliseconds
            conversation_id=conversation_id,
            message_type="assistant",
            content=content,
            sources=sources or [],
            tools=tools or [],
            created_at=now.isoformat()
        )
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert the model to a DynamoDB item format."""
        return {
            "user_id": {"S": self.user_id},
            "timestamp": {"N": str(self.timestamp)},
            "conversation_id": {"S": self.conversation_id},
            "message_type": {"S": self.message_type},
            "content": {"S": self.content},
            "sources": {"L": [{"M": source} for source in self.sources]} if self.sources else {"L": []},
            "tools": {"L": [{"M": tool} for tool in self.tools]} if self.tools else {"L": []},
            "created_at": {"S": self.created_at}
        }