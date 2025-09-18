"""
Model Factory for creating and configuring AI models

This factory provides a clean interface for instantiating different types of AI models
with appropriate configurations for the financial literacy chatbot.
"""

import os
from typing import Dict, Any, Optional
from .base_model import BaseModel, ModelConfig, ModelCapability, ModelName
from .google_genai_model import GoogleGenAIModel
from .embedding_model import EmbeddingModel

class ModelFactory:
    """Factory class for creating AI models with predefined configurations"""
    
    # Default model configurations
    DEFAULT_CONFIGS = {
        ModelName.GEMINI_FLASH: {
            "name": "Gemini Flash",
            "model_id": "gemini-2.5-flash",
            "capabilities": [
                ModelCapability.REASONING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.MULTILINGUAL
            ],
            "max_tokens": 8192,
            "temperature": 0.7,
            "is_primary": False,
            "priority": 2
        },
        
        # Gemma models
        ModelName.GEMMA_3N_2B: {
            "name": "Gemma 3N 2B",
            "model_id": "gemma-3n-2b-it",
            "capabilities": [
                ModelCapability.REASONING,
                ModelCapability.MULTILINGUAL,
                ModelCapability.EFFICIENT
            ],
            "max_tokens": 8192,
            "temperature": 0.7,
            "is_primary": False,
            "priority": 4
        },
        ModelName.GEMMA_3N_8B: {
            "name": "Gemma 3N 8B",
            "model_id": "gemma-3n-8b-it",
            "capabilities": [
                ModelCapability.REASONING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.MULTILINGUAL,
                ModelCapability.EFFICIENT
            ],
            "max_tokens": 8192,
            "temperature": 0.7,
            "is_primary": False,
            "priority": 5
        },
        ModelName.GEMMA_2B: {
            "name": "Gemma 2B",
            "model_id": "gemma-2b-it",
            "capabilities": [
                ModelCapability.REASONING,
                ModelCapability.MULTILINGUAL,
                ModelCapability.EFFICIENT
            ],
            "max_tokens": 8192,
            "temperature": 0.7,
            "is_primary": False,
            "priority": 6
        },
        ModelName.GEMMA_7B: {
            "name": "Gemma 7B",
            "model_id": "gemma-7b-it",
            "capabilities": [
                ModelCapability.REASONING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.MULTILINGUAL
            ],
            "max_tokens": 8192,
            "temperature": 0.7,
            "is_primary": False,
            "priority": 7
        }
    }
    
    @classmethod
    def create_google_genai_model(
        cls,
        model_name: ModelName = ModelName.GEMINI_PRO,
        api_key: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> GoogleGenAIModel:
        """Create a Google GenAI model (Gemini or Gemma) with the specified configuration"""
        
        # Get base config
        config_dict = cls.DEFAULT_CONFIGS[model_name].copy()
        
        # Apply custom configuration if provided
        if custom_config:
            config_dict.update(custom_config)
        
        # Create ModelConfig object
        config = ModelConfig(
            name=config_dict["name"],
            model_id=config_dict["model_id"],
            capabilities=config_dict["capabilities"],
            max_tokens=config_dict["max_tokens"],
            temperature=config_dict["temperature"],
            is_primary=config_dict["is_primary"],
            priority=config_dict["priority"]
        )
        
        # Get API key
        api_key = api_key or os.getenv("GOOGLE_GENAI_API_KEY")
        if not api_key:
            raise ValueError("Google GenAI API key is required. Set GOOGLE_GENAI_API_KEY environment variable or pass api_key parameter.")
        
        return GoogleGenAIModel(config, api_key)
    
    @classmethod
    def create_gemini_model(
        cls,
        model_name: ModelName = ModelName.GEMINI_PRO,
        api_key: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> GoogleGenAIModel:
        """Create a Gemini model (alias for create_google_genai_model)"""
        return cls.create_google_genai_model(model_name, api_key, custom_config)
    
    @classmethod
    def create_gemma_model(
        cls,
        model_name: ModelName = ModelName.GEMMA_3N_2B,
        api_key: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> GoogleGenAIModel:
        """Create a Gemma model with the specified configuration"""
        
        # Validate that it's a Gemma model
        if "gemma" not in model_name.value.lower():
            raise ValueError(f"Model {model_name.value} is not a Gemma model")
        
        return cls.create_google_genai_model(model_name, api_key, custom_config)
    
    @classmethod
    def create_embedding_model(
        cls,
        model_name: str = "intfloat/multilingual-E5-large",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> EmbeddingModel:
        """Create an embedding model with the specified configuration"""
        
        # Default embedding model config
        config_dict = {
            "name": "multilingual-e5-large",
            "model_id": model_name,
            "capabilities": [ModelCapability.MULTILINGUAL],
            "max_tokens": 512,
            "temperature": 0.0,
            "is_primary": True,
            "priority": 1
        }
        
        # Apply custom configuration if provided
        if custom_config:
            config_dict.update(custom_config)
        
        # Create ModelConfig object
        config = ModelConfig(
            name=config_dict["name"],
            model_id=config_dict["model_id"],
            capabilities=config_dict["capabilities"],
            max_tokens=config_dict["max_tokens"],
            temperature=config_dict["temperature"],
            is_primary=config_dict["is_primary"],
            priority=config_dict["priority"]
        )
        
        return EmbeddingModel(config)
    
    @classmethod
    def create_default_models(cls, api_key: Optional[str] = None) -> Dict[str, BaseModel]:
        """Create default models for the chatbot"""
        
        models = {}
        
        try:
            # Create primary Gemini model
            models["llm"] = cls.create_google_genai_model(
                model_name=ModelName.GEMINI_FLASH,
                api_key=api_key
            )
            
            # Create embedding model
            models["embedding"] = cls.create_embedding_model()
            
        except Exception as e:
            raise RuntimeError(f"Failed to create default models: {e}")
        
        return models
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about all available models"""
        return {
            name.value: config for name, config in cls.DEFAULT_CONFIGS.items()
        }
    
    @classmethod
    def get_gemini_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about available Gemini models"""
        return {
            name.value: config for name, config in cls.DEFAULT_CONFIGS.items()
            if "gemini" in name.value.lower()
        }
    
    @classmethod
    def get_gemma_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about available Gemma models"""
        return {
            name.value: config for name, config in cls.DEFAULT_CONFIGS.items()
            if "gemma" in name.value.lower()
        }
