"""
AI Models Module for Financial Literacy Chatbot

This module provides a clean interface for different AI models including:
- LLM models (Gemini, Gemma)
- Embedding models for RAG
- Model factory for easy instantiation
"""

from .base_model import BaseModel, ModelConfig, ModelResponse, ModelCapability, ModelName
from .google_genai_model import GoogleGenAIModel
from .embedding_model import EmbeddingModel
from .model_factory import ModelFactory
from .model_manager import ModelManager

# Backward compatibility aliases
GeminiModel = GoogleGenAIModel

__all__ = [
    "BaseModel",
    "ModelConfig", 
    "ModelResponse",
    "ModelCapability",
    "ModelName",
    "GoogleGenAIModel",
    "GeminiModel",  # Backward compatibility
    "EmbeddingModel",
    "ModelFactory",
    "ModelManager"
]
