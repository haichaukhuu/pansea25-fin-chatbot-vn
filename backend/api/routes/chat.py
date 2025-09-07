"""
Chat API routes for AgriFinHub Chatbot
Handles chat interactions and streaming responses
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging

# Import AI model components
from ai_models.model_manager import ModelManager

logger = logging.getLogger(__name__)

# Create router
chat_router = APIRouter(prefix="/chat", tags=["chat"])

# Security
security = HTTPBearer()

# Pydantic models
class ChatMessage(BaseModel):
    role: str  # "user" or "bot"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []
    user_profile: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    response: str
    model_used: str
    confidence_score: float
    usage_stats: Dict[str, Any]

# Initialize model manager (will be injected as dependency)
model_manager = None

def get_model_manager() -> ModelManager:
    """Dependency to get model manager instance"""
    global model_manager
    if model_manager is None:
        try:
            model_manager = ModelManager()
        except Exception as e:
            logger.error(f"Failed to get model manager: {str(e)}")
            raise HTTPException(status_code=503, detail="AI models not available")
    return model_manager

def set_model_manager(manager: ModelManager):
    """Set the model manager instance"""
    global model_manager
    model_manager = manager

@chat_router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """Main chat endpoint"""
    # Check if any models are available
    available_models = model_manager.get_available_models()
    if not available_models:
        logger.error("No AI models available for chat")
        raise HTTPException(status_code=503, detail="No AI models available")
    
    try:
        logger.info(f"Chat request received: {request.message[:50]}...")
        
        # Prepare context
        context = {
            "chat_history": request.chat_history,
            "user_profile": request.user_profile or {}
        }
        
        # Generate response using the primary model
        response = await model_manager.generate_response(
            prompt=request.message,
            context=context
        )
        
        logger.info(f"Chat response generated using model: {response.model_used}")

        return ChatResponse(
            response=response.content,
            model_used=response.model_used,
            confidence_score=response.confidence_score,
            usage_stats=response.usage_stats
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

@chat_router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """Streaming chat endpoint using Server-Sent Events"""
    try:
        logger.info(f"Streaming chat request received: {request.message[:50]}...")
        
        # Prepare context
        context = {
            "chat_history": request.chat_history,
            "user_profile": request.user_profile or {}
        }
        
        # Generate streaming response
        async def generate():
            try:
                async for chunk in model_manager.generate_streaming_response(
                    prompt=request.message,
                    context=context
                ):
                    # Format as SSE data
                    yield f"data: {json.dumps({'content': chunk, 'type': 'content'})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                logger.info("Completed streaming response")
                
            except Exception as e:
                logger.error(f"Streaming generation error: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate streaming response: {str(e)}")
