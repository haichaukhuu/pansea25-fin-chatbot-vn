# backend/ai_models/base_model.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, AsyncIterator
from dataclasses import dataclass
import asyncio
from enum import Enum
from pydantic import BaseModel as PydanticBaseModel

class ModelName(Enum):
    # Gemini models
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    
    # Gemma models
    GEMMA_3N_2B = "gemma-3n-2b-it"
    GEMMA_3N_8B = "gemma-3n-8b-it"
    GEMMA_2B = "gemma-2b-it"
    GEMMA_7B = "gemma-7b-it"

class ModelCapability(Enum):
    REASONING = "reasoning"
    TOOL_CALLING = "tool_calling"
    LONG_CONTEXT = "long_context"
    CREATIVE_RESPONSE = "creative_response"
    SUCCINCT_RESPONSE = "succinct_response"
    MULTILINGUAL = "multilingual"
    VISION = "vision"
    EFFICIENT = "efficient"  # For smaller, faster models like Gemma
    CHAT = "chat"  # For chat-based models
    TEXT_GENERATION = "text_generation"  # For text generation models

@dataclass
class ModelResponse:
    content: str
    model_used: str
    usage_stats: Dict[str, Any]
    confidence_score: Optional[float] = None
    is_fallback: bool = False
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ModelConfig:
    name: str
    model_id: str
    capabilities: List[ModelCapability]
    max_tokens: int
    temperature: float
    is_primary: bool = True
    priority: int = 1  # Lower number = higher priority
    api_key: Optional[str] = None

class BaseModel(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config
        self.is_available = True
        self.error_count = 0
        self.max_errors = 3
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None,
        system_prompt: str = None,
        tools: List[Dict] = None
    ) -> ModelResponse:
        """Generate text response from the model"""
        pass
    
    @abstractmethod
    async def generate_streaming_response(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        system_prompt: str = None
    ) -> AsyncIterator[str]:
        """Generate streaming response from the model"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for the text"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if model is available and healthy"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.config.name,
            "model_id": self.config.model_id,
            "capabilities": [cap.value for cap in self.config.capabilities],
            "is_available": self.is_available,
            "is_primary": self.config.is_primary,
            "priority": self.config.priority
        }
    
    def mark_error(self):
        """Mark model as having an error"""
        self.error_count += 1
        if self.error_count >= self.max_errors:
            self.is_available = False
    
    def reset_errors(self):
        """Reset error count and mark as available"""
        self.error_count = 0
        self.is_available = True
