"""
LLM Client - Unified interface for interacting with various LLM providers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
import os
import logging

from .base_model import BaseAIModel
from .model_factory import ModelFactory
from .model_manager import ModelManager

logger = logging.getLogger(__name__)

class LLMClient:
    """
    A unified client for interacting with various LLM providers.
    This class provides a clean interface for sending prompts to different
    models and handling responses in a consistent way.
    """
    
    def __init__(self, default_model_name: str = "gemini-pro"):
        """
        Initialize the LLM client.
        
        Args:
            default_model_name (str): The default model to use when none is specified
        """
        self.model_manager = ModelManager()
        self.model_factory = ModelFactory()
        self.default_model_name = default_model_name
        
    def get_model(self, model_name: Optional[str] = None) -> BaseAIModel:
        """
        Get an instance of the requested model.
        
        Args:
            model_name (str, optional): The name of the model to use.
                                       If None, uses the default model.
                                       
        Returns:
            BaseAIModel: The requested model instance
        """
        model_name = model_name or self.default_model_name
        return self.model_factory.get_model(model_name)
    
    def send_message(
        self, 
        prompt: str, 
        model_name: Optional[str] = None, 
        temperature: float = 0.7, 
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Send a message to the specified LLM and get a response.
        
        Args:
            prompt (str): The message to send to the model
            model_name (str, optional): The name of the model to use
            temperature (float): Controls randomness (0.0-1.0)
            max_tokens (int, optional): Maximum number of tokens to generate
            **kwargs: Additional model-specific parameters
            
        Returns:
            str: The model's response
        """
        model = self.get_model(model_name)
        
        try:
            response = model.generate_text(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Error generating text with model {model_name}: {str(e)}")
            raise
    
    def list_available_models(self) -> List[str]:
        """
        Get a list of all available models.
        
        Returns:
            List[str]: Names of available models
        """
        return self.model_manager.list_models()
    
    def get_embeddings(self, text: Union[str, List[str]], model_name: Optional[str] = None) -> List[List[float]]:
        """
        Generate embeddings for the given text using the specified embedding model.
        
        Args:
            text (str or List[str]): Text to generate embeddings for
            model_name (str, optional): Name of the embedding model to use
            
        Returns:
            List[List[float]]: The generated embeddings
        """
        model_name = model_name or "embedding-model"  # Use default embedding model
        model = self.get_model(model_name)
        
        try:
            if not hasattr(model, "get_embeddings"):
                raise AttributeError(f"Model {model_name} does not support embeddings")
                
            return model.get_embeddings(text)
        except Exception as e:
            logger.error(f"Error generating embeddings with model {model_name}: {str(e)}")
            raise