import uuid
import json
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
    
    def _convert_to_dynamodb_format(self, obj: Any) -> Dict[str, Any]:
        """Convert a Python object to DynamoDB format with proper type annotations."""
        if isinstance(obj, bool):  # Check bool before int since bool is subclass of int
            return {"BOOL": obj}
        elif isinstance(obj, str):
            return {"S": obj}
        elif isinstance(obj, (int, float)):
            return {"N": str(obj)}
        elif isinstance(obj, list):
            return {"L": [self._convert_to_dynamodb_format(item) for item in obj]}
        elif isinstance(obj, dict):
            return {"M": {k: self._convert_to_dynamodb_format(v) for k, v in obj.items()}}
        elif obj is None:
            return {"NULL": True}
        else:
            # Fallback: convert to string
            return {"S": str(obj)}

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert the model to a DynamoDB item format."""
        return {
            "user_id": {"S": self.user_id},
            "timestamp": {"N": str(self.timestamp)},
            "conversation_id": {"S": self.conversation_id},
            "message_type": {"S": self.message_type},
            "content": {"S": self.content},
            "sources": {"S": json.dumps(self.sources) if self.sources else "[]"},
            "tools": {"S": json.dumps(self.tools) if self.tools else "[]"},
            "created_at": {"S": self.created_at}
        }

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "ChatHistoryItem":
        """Create a ChatHistoryItem from a DynamoDB item."""
        try:
            sources = json.loads(item.get('sources', {}).get('S', '[]'))
        except (json.JSONDecodeError, KeyError):
            sources = []
            
        try:
            tools = json.loads(item.get('tools', {}).get('S', '[]'))
        except (json.JSONDecodeError, KeyError):
            tools = []

        return cls(
            user_id=item.get('user_id', {}).get('S', ''),
            timestamp=int(item.get('timestamp', {}).get('N', '0')),
            conversation_id=item.get('conversation_id', {}).get('S', ''),
            message_type=item.get('message_type', {}).get('S', ''),
            content=item.get('content', {}).get('S', ''),
            sources=sources,
            tools=tools,
            created_at=item.get('created_at', {}).get('S', '')
        )