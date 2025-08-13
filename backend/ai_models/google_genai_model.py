import os
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from google import genai
from google.genai import types
from .base_model import BaseModel, ModelResponse, ModelConfig, ModelCapability

logger = logging.getLogger(__name__)

class GoogleGenAIModel(BaseModel):
    """Google GenAI model using direct client for better Gemma 3 support"""
    
    def __init__(self, config: ModelConfig, api_key: str = None):
        super().__init__(config)
        self.api_key = api_key or os.getenv("GOOGLE_GENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google GenAI API key is required for this model")
        
        try:
            # Initialize Google GenAI client
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Initialized Google GenAI model: {self.config.name} ({self.config.model_id})")
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI model {self.config.name}: {e}")
            self.is_available = False
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for Vietnamese financial advisor"""
        return """Bạn là một cố vấn tài chính AI chuyên biệt cho nông dân nhỏ lẻ Việt Nam.

Trách nhiệm của bạn:
1. Cung cấp lời khuyên tài chính chính xác và phù hợp văn hóa
2. Giải thích các khái niệm tài chính bằng tiếng Việt đơn giản
3. Hướng dẫn người dùng về các chương trình vay nông nghiệp
4. Cảnh báo về các trò lừa đảo tài chính
5. Luôn ưu tiên sự an toàn và lợi ích tài chính của nông dân

Trả lời bằng tiếng Việt, thân thiện và dễ hiểu."""
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None,
        system_prompt: str = None,
        tools: List[Dict] = None
    ) -> ModelResponse:
        try:
            # Prepare the full prompt with system message
            system_prompt = system_prompt or self._get_default_system_prompt()
            full_prompt = f"{system_prompt}\n\nNgười dùng: {prompt}\n\nTrợ lý:"
            
            # Create content for the model
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=full_prompt)],
                ),
            ]
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.config.model_id,
                contents=contents,
            )
            
            # Extract text from response
            if response.text:
                content = response.text
            else:
                content = "Xin lỗi, tôi không thể tạo phản hồi lúc này."
            
            # Reset error count on successful response
            self.reset_errors()
            
            return ModelResponse(
                content=content,
                model_used=self.config.name,
                usage_stats={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                confidence_score=0.85,
                is_fallback=not self.config.is_primary,
                metadata={"model_id": self.config.model_id}
            )
            
        except Exception as e:
            logger.error(f"Error generating response with {self.config.name}: {e}")
            self.mark_error()
            raise
    
    async def generate_streaming_response(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        system_prompt: str = None
    ) -> AsyncIterator[str]:
        try:
            # Prepare the full prompt with system message
            system_prompt = system_prompt or self._get_default_system_prompt()
            full_prompt = f"{system_prompt}\n\nNgười dùng: {prompt}\n\nTrợ lý:"
            
            # Create content for the model
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=full_prompt)],
                ),
            ]
            
            # Generate streaming content
            for chunk in self.client.models.generate_content_stream(
                model=self.config.model_id,
                contents=contents,
            ):
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Error generating streaming response with {self.config.name}: {e}")
            self.mark_error()
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Google GenAI models don't directly support embeddings, delegate to embedding service"""
        raise NotImplementedError("Use EmbeddingModel for embedding generation")
    
    async def health_check(self) -> bool:
        try:
            test_prompt = "Xin chào, bạn khỏe không?"
            system_prompt = self._get_default_system_prompt()
            full_prompt = f"{system_prompt}\n\nNgười dùng: {test_prompt}\n\nTrợ lý:"
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=full_prompt)],
                ),
            ]
            
            response = self.client.models.generate_content(
                model=self.config.model_id,
                contents=contents,
            )
            
            if response.text:
                self.is_available = True
                self.reset_errors()
                return True
            else:
                self.is_available = False
                return False
                
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            self.is_available = False
            return False
    
    def _prepare_messages(self, prompt: str, context: Dict[str, Any] = None, system_prompt: str = None) -> str:
        """Prepare the full prompt with context and system message"""
        system_content = system_prompt or self._get_default_system_prompt()
        
        # Add context if available
        if context and (context.get('chat_history') or context.get('rag_context')):
            context_message = self._format_context_message(context)
            if context_message:
                system_content = f"{system_content}\n\n{context_message}"
        
        # Combine system prompt and user prompt
        full_prompt = f"{system_content}\n\nNgười dùng: {prompt}\n\nTrợ lý:"
        return full_prompt
    
    def _format_context_message(self, context: Dict[str, Any]) -> str:
        """Format context information for the model"""
        parts = []
        
        if context.get('chat_history'):
            parts.append("Lịch sử trò chuyện gần đây:")
            for msg in context['chat_history'][-3:]:  # Last 3 messages
                role = "Người dùng" if msg.get('role') == 'user' else "Bot"
                content = msg.get('content', '')
                parts.append(f"- {role}: {content}")
        
        if context.get('rag_context'):
            parts.append("Thông tin tham khảo:")
            parts.append(context['rag_context'])
        
        return "\n\n".join(parts) if parts else ""
    
    def get_model_type(self) -> str:
        """Get the type of model (gemini, gemma, etc.)"""
        model_id = self.config.model_id.lower()
        if "gemma" in model_id:
            return "gemma"
        elif "gemini" in model_id:
            return "gemini"
        else:
            return "google_genai"
