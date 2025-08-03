from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio

@dataclass
class ModelResponse:
    """Standardized response format for all models"""
    content: str
    confidence: float
    model_used: str
    tokens_used: int
    processing_time: float
    metadata: Dict[str, Any] = None

class ModelConfig:
    """Configuration for model initialization"""
    model_name: str
    api_key: str
    endpoint: str
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 60

class BaseModel(ABC):
    """Abstract base class for all AI models"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model_name = config.model_name
        
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response from model"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if model is available"""
        pass