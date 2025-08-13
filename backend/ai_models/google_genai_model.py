import os
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks import AsyncIteratorCallbackHandler
from .base_model import BaseModel, ModelResponse, ModelConfig, ModelCapability

logger = logging.getLogger(__name__)

class GoogleGenAIModel(BaseModel):
    """Generalized Google GenAI model supporting both Gemini and Gemma models"""
    
    def __init__(self, config: ModelConfig, api_key: str = None):
        super().__init__(config)
        self.api_key = api_key or os.getenv("GOOGLE_GENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google GenAI API key is required for this model")
        
        try:
            # Initialize LangChain Google GenAI model
            self.model = ChatGoogleGenerativeAI(
                model=self.config.model_id,
                google_api_key=self.api_key,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                convert_system_message_to_human=True,  # Google models don't support system messages natively
                streaming=True
            )
            logger.info(f"Initialized Google GenAI model: {self.config.name} ({self.config.model_id})")
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI model {self.config.name}: {e}")
            self.is_available = False
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt based on model type"""
        if "gemma" in self.config.model_id.lower():
            return """Bạn là một cố vấn tài chính AI chuyên biệt cho nông dân nhỏ lẻ Việt Nam.
            
            Trách nhiệm của bạn:
            1. Cung cấp lời khuyên tài chính chính xác và phù hợp văn hóa
            2. Giải thích các khái niệm tài chính bằng tiếng Việt đơn giản
            3. Hướng dẫn người dùng về các chương trình vay nông nghiệp
            4. Cảnh báo về các trò lừa đảo tài chính
            5. Luôn ưu tiên sự an toàn và lợi ích tài chính của nông dân
            
            Trả lời bằng tiếng Việt, thân thiện và dễ hiểu."""
        else:
            # Default Gemini prompt
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
            # Prepare messages
            messages = self._prepare_messages(prompt, context, system_prompt)
            
            # Generate response
            response = await self.model.agenerate([messages])
            
            # Extract content and usage stats
            content = response.generations[0][0].text
            usage_stats = self._extract_usage_stats(response)
            
            # Reset error count on successful response
            self.reset_errors()
            
            return ModelResponse(
                content=content,
                model_used=self.config.name,
                usage_stats=usage_stats,
                confidence_score=0.85,  # Default confidence for Google models
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
            # Prepare messages
            messages = self._prepare_messages(prompt, context, system_prompt)
            
            # Create streaming callback handler
            callback = AsyncIteratorCallbackHandler()
            
            # Generate streaming response
            async for chunk in self.model.astream(messages, callbacks=[callback]):
                if chunk.content:
                    yield chunk.content
                    
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
            messages = [HumanMessage(content=test_prompt)]
            response = await self.model.agenerate([messages])
            
            if response.generations and response.generations[0]:
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
    
    def _prepare_messages(self, prompt: str, context: Dict[str, Any] = None, system_prompt: str = None) -> List:
        """Prepare messages for the model"""
        messages = []
        
        # Add system prompt
        system_content = system_prompt or self._get_default_system_prompt()
        if context:
            system_content = self._enhance_system_prompt(system_content, context)
        
        messages.append(SystemMessage(content=system_content))
        
        # Add context as human message if available
        if context and (context.get('chat_history') or context.get('rag_context')):
            context_message = self._format_context_message(context)
            if context_message:
                messages.append(HumanMessage(content=context_message))
        
        # Add the main prompt
        messages.append(HumanMessage(content=prompt))
        
        return messages
    
    def _enhance_system_prompt(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """Enhance system prompt with context information"""
        enhancements = []
        
        if context.get('user_profile'):
            profile = context['user_profile']
            location = profile.get('location', 'Việt Nam')
            farming_type = profile.get('farming_type', 'nông nghiệp')
            enhancements.append(f"Người dùng ở {location}, làm {farming_type}")
        
        if context.get('rag_context'):
            enhancements.append("Bạn có quyền truy cập vào thông tin tham khảo để trả lời câu hỏi.")
        
        if enhancements:
            enhanced_prompt = base_prompt + "\n\n" + "\n".join(enhancements)
            return enhanced_prompt
        
        return base_prompt
    
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
    
    def _extract_usage_stats(self, response) -> Dict[str, Any]:
        """Extract usage statistics from response"""
        try:
            # LangChain doesn't always provide detailed usage stats for Google models
            # We'll return what we can extract
            usage_stats = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
            
            # Try to extract from response metadata if available
            if hasattr(response, 'llm_output') and response.llm_output:
                if 'token_usage' in response.llm_output:
                    usage_stats.update(response.llm_output['token_usage'])
            
            return usage_stats
            
        except Exception as e:
            logger.warning(f"Could not extract usage stats: {e}")
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
    
    def get_model_type(self) -> str:
        """Get the type of model (gemini, gemma, etc.)"""
        model_id = self.config.model_id.lower()
        if "gemma" in model_id:
            return "gemma"
        elif "gemini" in model_id:
            return "gemini"
        else:
            return "google_genai"
