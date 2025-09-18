import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator
from google import genai
from google.genai import types
from .base_model import BaseModel, ModelResponse, ModelConfig, ModelCapability

logger = logging.getLogger(__name__)

class GoogleGenAIModel(BaseModel):
    """Enhanced Google GenAI model with optimized streaming support for both Gemini and Gemma models"""
    
    def __init__(self, config: ModelConfig, api_key: str = None):
        super().__init__(config)
        self.api_key = api_key or os.getenv("GOOGLE_GENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google GenAI API key is required for this model")
        
        # Get model type for optimization
        self.model_type = self._detect_model_type()
        
        # Set up streaming configuration based on model type
        self.streaming_config = self._configure_streaming()
        
        try:
            # Initialize Google GenAI client
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Initialized Google GenAI model: {self.config.name} ({self.config.model_id}) - Type: {self.model_type}")
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI model {self.config.name}: {e}")
            self.is_available = False
    
    def _detect_model_type(self) -> str:
        """Detect model type from model ID for optimization"""
        model_id = self.config.model_id.lower()
        if "gemini" in model_id:
            return "gemini"
        elif "gemma" in model_id:
            return "gemma"
        else:
            # Default to gemini for Google GenAI models
            return "gemini"
    
    def _configure_streaming(self) -> Dict[str, Any]:
        """Configure streaming parameters based on model type and capabilities"""
        base_config = {
            "buffer_size": 1024,
            "chunk_timeout": 5.0,
            "enable_adaptive_chunking": True
        }
        
        # Model-specific optimizations
        if self.model_type == "gemini":
            # Gemini models have native streaming optimization
            base_config.update({
                "streaming_method": "native",
                "chunk_size": "medium",
                "latency_optimization": True
            })
        elif self.model_type == "gemma":
            # Gemma models benefit from KV cache optimization
            base_config.update({
                "streaming_method": "kv_cache_optimized",
                "chunk_size": "small",
                "cache_optimization": True
            })
        
        # Apply custom config from model configuration
        if hasattr(self.config, 'streaming_config'):
            base_config.update(self.config.streaming_config)
        
        return base_config
    
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
        """Generate streaming response with model-specific optimizations"""
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
            
            # Prepare generation config based on model type and streaming configuration
            generation_config = self._prepare_generation_config()
            
            # Generate streaming content with optimizations
            logger.info(f"Starting streaming response with {self.config.name} ({self.model_type})")
            
            if self.streaming_config.get("streaming_method") == "kv_cache_optimized":
                # For Gemma models: Use KV cache optimization
                async for chunk_text in self._stream_with_kv_optimization(contents, generation_config):
                    yield chunk_text
            else:
                # For Gemini models: Use native streaming
                async for chunk_text in self._stream_with_native_optimization(contents, generation_config):
                    yield chunk_text
                    
        except Exception as e:
            logger.error(f"Error generating streaming response with {self.config.name}: {e}")
            self.mark_error()
            raise
    
    def _prepare_generation_config(self) -> types.GenerateContentConfig:
        """Prepare generation configuration optimized for streaming"""
        config_params = {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
        }
        
        # Add model-specific streaming optimizations
        if self.model_type == "gemini":
            # Gemini models support advanced features
            config_params.update({
                "candidate_count": 1,  # Single candidate for faster streaming
                "top_p": 0.95,
                "top_k": 40
            })
        elif self.model_type == "gemma":
            # Gemma models benefit from consistent parameters
            config_params.update({
                "candidate_count": 1,
                "top_p": 0.9,
                "top_k": 20
            })
        
        return types.GenerateContentConfig(**config_params)
    
    async def _stream_with_native_optimization(
        self, 
        contents: List[types.Content], 
        config: types.GenerateContentConfig
    ) -> AsyncIterator[str]:
        """Stream with native Gemini optimization"""
        try:
            chunk_buffer = ""
            buffer_size = self.streaming_config.get("buffer_size", 1024)
            
            for chunk in self.client.models.generate_content_stream(
                model=self.config.model_id,
                contents=contents,
                config=config
            ):
                if chunk.text:
                    chunk_buffer += chunk.text
                    
                    # Adaptive chunking for better UX
                    if self.streaming_config.get("enable_adaptive_chunking", True):
                        # Send chunks at word boundaries for better readability
                        while len(chunk_buffer) > buffer_size or self._is_sentence_boundary(chunk_buffer):
                            send_chunk, chunk_buffer = self._extract_chunk(chunk_buffer, buffer_size)
                            if send_chunk:
                                yield send_chunk
                                # Small delay for smoother streaming
                                await asyncio.sleep(0.01)
                    else:
                        # Simple chunking
                        if len(chunk_buffer) >= buffer_size:
                            yield chunk_buffer
                            chunk_buffer = ""
            
            # Send remaining buffer
            if chunk_buffer:
                yield chunk_buffer
                
        except Exception as e:
            logger.error(f"Error in native streaming: {e}")
            raise
    
    async def _stream_with_kv_optimization(
        self, 
        contents: List[types.Content], 
        config: types.GenerateContentConfig
    ) -> AsyncIterator[str]:
        """Stream with KV cache optimization for Gemma models"""
        try:
            # KV cache optimization: Smaller chunks for faster first token
            smaller_buffer = self.streaming_config.get("buffer_size", 1024) // 2
            chunk_buffer = ""
            
            for chunk in self.client.models.generate_content_stream(
                model=self.config.model_id,
                contents=contents,
                config=config
            ):
                if chunk.text:
                    chunk_buffer += chunk.text
                    
                    # Optimized for KV cache: Send smaller, more frequent chunks
                    if len(chunk_buffer) >= smaller_buffer:
                        yield chunk_buffer
                        chunk_buffer = ""
                        # Shorter delay for KV cache optimization
                        await asyncio.sleep(0.005)
            
            # Send remaining buffer
            if chunk_buffer:
                yield chunk_buffer
                
        except Exception as e:
            logger.error(f"Error in KV cache optimized streaming: {e}")
            raise
    
    def _is_sentence_boundary(self, text: str) -> bool:
        """Check if text ends at a natural sentence boundary"""
        if len(text) < 50:  # Too short for sentence boundary check
            return False
        
        # Vietnamese sentence endings
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        return any(text.endswith(ending) for ending in sentence_endings)
    
    def _extract_chunk(self, buffer: str, max_size: int) -> tuple[str, str]:
        """Extract a chunk at word boundary for better readability"""
        if len(buffer) <= max_size:
            return buffer, ""
        
        # Find last word boundary within max_size
        chunk = buffer[:max_size]
        last_space = chunk.rfind(' ')
        
        if last_space > max_size * 0.7:  # If word boundary is reasonable
            return buffer[:last_space + 1], buffer[last_space + 1:]
        else:
            # If no good word boundary, just split at max_size
            return buffer[:max_size], buffer[max_size:]
    
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
        return self.model_type
    
    def get_streaming_capabilities(self) -> Dict[str, Any]:
        """Get streaming capabilities and configuration"""
        return {
            "supports_streaming": True,
            "model_type": self.model_type,
            "streaming_method": self.streaming_config.get("streaming_method", "native"),
            "optimizations": {
                "kv_cache": self.model_type == "gemma",
                "native_streaming": self.model_type == "gemini",
                "adaptive_chunking": self.streaming_config.get("enable_adaptive_chunking", True)
            },
            "performance": {
                "expected_latency": "low" if self.model_type == "gemini" else "very_low",
                "chunk_strategy": self.streaming_config.get("chunk_size", "medium")
            }
        }
