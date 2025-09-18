"""
Model Manager for orchestrating multiple AI models

This manager provides a unified interface for working with different types of AI models,
handling fallbacks, and managing model health.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from .base_model import BaseModel, ModelResponse, ModelCapability
from .model_factory import ModelFactory

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages multiple AI models with fallback and health monitoring"""
    
    def __init__(self):
        self.models: Dict[str, BaseModel] = {}
        self.model_types: Dict[str, str] = {}  # Maps model name to type (llm, embedding, etc.)
        self.health_check_interval = 300  # 5 minutes
        self._health_check_task = None
        
        logger.info("ModelManager initializing...")
        # Initialize with default models
        self._initialize_default_models()
        logger.info(f"ModelManager initialized with {len(self.models)} models: {list(self.models.keys())}")
    
    def _initialize_default_models(self):
        """Initialize with default models from config"""
        try:
            import os
            from .google_genai_model import GoogleGenAIModel
            from .base_model import ModelConfig, ModelCapability
            
            # Get API key directly from environment
            api_key = os.getenv("GOOGLE_GENAI_API_KEY")
            if not api_key:
                logger.error("No GOOGLE_GENAI_API_KEY found in environment")
                return
            
            # Create Gemma 3 model (primary)
            gemma_3_config = ModelConfig(
                name="Gemma 3 27B IT",
                model_id="gemma-3-27b-it",
                temperature=0.7,
                max_tokens=4096,
                is_primary=True,
                capabilities=[ModelCapability.CHAT, ModelCapability.TEXT_GENERATION],
                priority=1
            )
            
            gemma_3_model = GoogleGenAIModel(gemma_3_config, api_key)
            self.add_model("gemma_3", gemma_3_model, "llm")
            logger.info("Initialized Gemma 3 model successfully")
            
            # Create Gemini model (fallback)
            gemini_pro_config = ModelConfig(
                name="Gemini 2.5 Flash",
                model_id="gemini-2.5-flash",
                temperature=0.6,
                max_tokens=8192,
                is_primary=False,
                capabilities=[ModelCapability.CHAT, ModelCapability.TEXT_GENERATION],
                priority=2
            )
            
            gemini_pro_model = GoogleGenAIModel(gemini_pro_config, api_key)
            self.add_model("gemini_pro", gemini_pro_model, "llm")
            logger.info("Initialized Gemini Pro model successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize default models: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def add_model(self, name: str, model: BaseModel, model_type: str = "llm"):
        """Add a model to the manager"""
        self.models[name] = model
        self.model_types[name] = model_type
        logger.info(f"Added {model_type} model: {name}")
    
    def get_model(self, name: str) -> Optional[BaseModel]:
        """Get a specific model by name"""
        return self.models.get(name)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())
    
    def get_models_by_type(self, model_type: str) -> List[BaseModel]:
        """Get all models of a specific type"""
        return [
            model for name, model in self.models.items()
            if self.model_types.get(name) == model_type
        ]
    
    def get_primary_model(self, model_type: str = "llm") -> Optional[BaseModel]:
        """Get the primary model of a specific type"""
        models = self.get_models_by_type(model_type)
        primary_models = [m for m in models if m.config.is_primary]
        
        if primary_models:
            return primary_models[0]
        
        # If no primary model, return the first available one
        available_models = [m for m in models if m.is_available]
        return available_models[0] if available_models else None
    
    async def check_model_health(self, model_name: str) -> bool:
        """Check health of a specific model"""
        model = self.get_model(model_name)
        if not model:
            return False
        
        try:
            return await model.health_check()
        except Exception as e:
            logger.error(f"Health check failed for {model_name}: {e}")
            return False
    
    async def generate_response(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        system_prompt: str = None,
        tools: List[Dict] = None,
        model_type: str = "llm",
        preferred_model: str = None
    ) -> ModelResponse:
        """Generate response using the best available model"""
        
        # Try preferred model first if specified
        if preferred_model and preferred_model in self.models:
            model = self.models[preferred_model]
            if model.is_available and self.model_types.get(preferred_model) == model_type:
                try:
                    return await model.generate_response(prompt, context, system_prompt, tools)
                except Exception as e:
                    logger.warning(f"Preferred model {preferred_model} failed: {e}")
                    model.mark_error()
        
        # Get available models of the specified type
        available_models = [
            m for m in self.get_models_by_type(model_type)
            if m.is_available
        ]
        
        if not available_models:
            raise RuntimeError(f"No available {model_type} models")
        
        # Sort by priority (lower number = higher priority)
        available_models.sort(key=lambda m: getattr(m.config, 'priority', 999))
        
        # Try models in order of priority
        last_error = None
        for model in available_models:
            try:
                response = await model.generate_response(prompt, context, system_prompt, tools)
                logger.info(f"Generated response using {model.config.name}")
                return response
            except Exception as e:
                logger.warning(f"Model {model.config.name} failed: {e}")
                model.mark_error()
                last_error = e
        
        # All models failed
        raise RuntimeError(f"All {model_type} models failed. Last error: {last_error}")
    
    async def generate_streaming_response(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        system_prompt: str = None,
        model_type: str = "llm",
        preferred_model: str = None
    ) -> AsyncIterator[str]:
        """Generate enhanced streaming response with model-specific optimizations"""
        
        # Try preferred model first if specified
        if preferred_model and preferred_model in self.models:
            model = self.models[preferred_model]
            if model.is_available and self.model_types.get(preferred_model) == model_type:
                try:
                    logger.info(f"Using preferred model {preferred_model} for streaming")
                    async for chunk in model.generate_streaming_response(prompt, context, system_prompt):
                        yield chunk
                    return
                except Exception as e:
                    logger.warning(f"Preferred model {preferred_model} failed: {e}")
                    model.mark_error()
        
        # Get available models of the specified type
        available_models = [
            m for m in self.get_models_by_type(model_type)
            if m.is_available
        ]
        
        if not available_models:
            raise RuntimeError(f"No available {model_type} models")
        
        # Sort by priority, but prefer models with better streaming capabilities
        available_models.sort(key=lambda m: (
            getattr(m.config, 'priority', 999),
            0 if hasattr(m, 'get_streaming_capabilities') else 1
        ))
        
        # Try models in order of priority
        last_error = None
        for model in available_models:
            try:
                model_name = model.config.name
                model_type_info = getattr(model, 'model_type', 'unknown')
                logger.info(f"Starting streaming with {model_name} (type: {model_type_info})")
                
                # Log streaming capabilities if available
                if hasattr(model, 'get_streaming_capabilities'):
                    capabilities = model.get_streaming_capabilities()
                    logger.info(f"Streaming capabilities: {capabilities}")
                
                async for chunk in model.generate_streaming_response(prompt, context, system_prompt):
                    yield chunk
                
                logger.info(f"Successfully completed streaming response using {model_name}")
                return
                
            except Exception as e:
                logger.warning(f"Model {model.config.name} failed during streaming: {e}")
                model.mark_error()
                last_error = e
        
        # All models failed
        raise RuntimeError(f"All {model_type} models failed during streaming. Last error: {last_error}")
    
    def get_streaming_capabilities(self) -> Dict[str, Any]:
        """Get streaming capabilities summary for all models"""
        capabilities = {}
        
        for name, model in self.models.items():
            if hasattr(model, 'get_streaming_capabilities'):
                capabilities[name] = model.get_streaming_capabilities()
            else:
                capabilities[name] = {
                    "supports_streaming": True,
                    "model_type": "unknown",
                    "streaming_method": "basic"
                }
        
        return capabilities
    
    async def generate_embedding(
        self,
        text: str,
        model_type: str = "embedding",
        preferred_model: str = None
    ) -> List[float]:
        """Generate embedding using the best available embedding model"""
        
        # Try preferred model first if specified
        if preferred_model and preferred_model in self.models:
            model = self.models[preferred_model]
            if model.is_available and self.model_types.get(preferred_model) == model_type:
                try:
                    return await model.generate_embedding(text)
                except Exception as e:
                    logger.warning(f"Preferred model {preferred_model} failed: {e}")
                    model.mark_error()
        
        # Get available embedding models
        available_models = [
            m for m in self.get_models_by_type(model_type)
            if m.is_available
        ]
        
        if not available_models:
            raise RuntimeError(f"No available {model_type} models")
        
        # Sort by priority
        available_models.sort(key=lambda m: getattr(m.config, 'priority', 999))
        
        # Try models in order of priority
        last_error = None
        for model in available_models:
            try:
                embedding = await model.generate_embedding(text)
                logger.info(f"Generated embedding using {model.config.name}")
                return embedding
            except Exception as e:
                logger.warning(f"Model {model.config.name} failed: {e}")
                model.mark_error()
                last_error = e
        
        # All models failed
        raise RuntimeError(f"All {model_type} models failed. Last error: {last_error}")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all models"""
        results = {}
        
        for name, model in self.models.items():
            try:
                is_healthy = await model.health_check()
                results[name] = is_healthy
                logger.info(f"Health check for {name}: {'OK' if is_healthy else 'FAILED'}")
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        
        return results
    
    async def start_health_monitoring(self):
        """Start periodic health monitoring"""
        if self._health_check_task:
            return
        
        async def health_monitor():
            while True:
                try:
                    await self.health_check_all()
                    await asyncio.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
        
        self._health_check_task = asyncio.create_task(health_monitor())
        logger.info("Started health monitoring")
    
    def stop_health_monitoring(self):
        """Stop periodic health monitoring"""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None
            logger.info("Stopped health monitoring")
    
    def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all models"""
        status = {}
        
        for name, model in self.models.items():
            status[name] = {
                "type": self.model_types.get(name, "unknown"),
                "info": model.get_model_info(),
                "is_available": model.is_available,
                "error_count": model.error_count
            }
        
        return status
    
    @classmethod
    async def create_default_manager(cls, api_key: Optional[str] = None) -> 'ModelManager':
        """Create a model manager with default models"""
        manager = cls()
        
        try:
            # Create default models using factory
            default_models = ModelFactory.create_default_models(api_key)
            
            # Add models to manager
            for model_type, model in default_models.items():
                manager.add_model(model_type, model, model_type)
            
            # Start health monitoring
            await manager.start_health_monitoring()
            
            logger.info("Created default model manager with health monitoring")
            
        except Exception as e:
            logger.error(f"Failed to create default model manager: {e}")
            raise
        
        return manager
