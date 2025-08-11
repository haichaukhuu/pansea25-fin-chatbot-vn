import google.generativeai as genai
from typing import Dict, Any, List, Optional
from .base_model import BaseModel, ModelResponse, ModelConfig, ModelCapability
import logging

logger = logging.getLogger(__name__)

class GeminiModel(BaseModel):
    def __init__(self, config: ModelConfig, api_key: str):
        super().__init__(config)
        self.api_key = api_key
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name=self.config.model_id,
                system_instruction=self._get_system_instruction()
            )
            logger.info(f"Initialized Gemini model: {self.config.name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model {self.config.name}: {e}")
            self.is_available = False
    
    def _get_system_instruction(self) -> str:
        return """You are a specialized AI financial advisor for Vietnamese smallholder farmers.
        Your responsibilities:
        1. Provide accurate and culturally appropriate financial advice
        2. Explain financial concepts in simple Vietnamese
        3. Guide users about agricultural loan programs
        4. Warn about financial scams
        5. Always prioritize farmers' financial safety and interests
        
        Respond in Vietnamese, be friendly and easy to understand."""
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None,
        system_prompt: str = None,
        tools: List[Dict] = None
    ) -> ModelResponse:
        try:
            # Prepare the full prompt
            full_prompt = self._prepare_prompt(prompt, context, system_prompt)
            
            # Generation config
            generation_config = genai.GenerationConfig(
                max_output_tokens=min(self.config.max_tokens, 8192),
                temperature=self.config.temperature,
                top_p=0.95,
                top_k=40,
            )
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Extract usage stats (Gemini provides limited usage info)
            usage_stats = {
                "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
            }
            
            # Reset error count on successful response
            self.reset_errors()
            
            return ModelResponse(
                content=response.text,
                model_used=self.config.name,
                usage_stats=usage_stats,
                confidence_score=0.85,  # Default confidence for Gemini
                is_fallback=not self.config.is_primary
            )
            
        except Exception as e:
            logger.error(f"Error generating response with {self.config.name}: {e}")
            self.mark_error()
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Gemini doesn't directly support embeddings, delegate to embedding service"""
        raise NotImplementedError("Use EmbeddingModel for embedding generation")
    
    async def health_check(self) -> bool:
        try:
            test_prompt = "Hello, how are you?"
            response = self.model.generate_content(
                test_prompt,
                generation_config=genai.GenerationConfig(max_output_tokens=10)
            )
            self.is_available = True
            self.reset_errors()
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            self.is_available = False
            return False
    
    def _prepare_prompt(self, prompt: str, context: Dict[str, Any] = None, system_prompt: str = None) -> str:
        """Prepare the full prompt with context"""
        parts = []
        
        if system_prompt:
            parts.append(f"System instruction: {system_prompt}")
        
        if context:
            if context.get('chat_history'):
                parts.append("Chat history:")
                for msg in context['chat_history'][-5:]:
                    parts.append(f"- {msg.get('role', 'user')}: {msg.get('content', '')}")
            
            if context.get('rag_context'):
                parts.append("Reference information:")
                parts.append(context['rag_context'])
            
            if context.get('user_profile'):
                profile = context['user_profile']
                parts.append(f"User info: {profile.get('location', '')}, {profile.get('farming_type', '')}")
        
        parts.append(f"Question: {prompt}")
        
        return "\n\n".join(parts)
