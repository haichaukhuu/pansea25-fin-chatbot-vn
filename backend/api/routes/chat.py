from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import logging
import uuid
from datetime import datetime

# Import ReAct agent components
from agent.agent_service import AgentService
from agent.react_agent import FinancialAgentResponse
from core.services.chat_history_service import ChatHistoryService
from api.middleware.auth_middleware import get_current_user
from database.models.user import User

# Legacy import for backward compatibility
from ai_models.model_manager import ModelManager

logger = logging.getLogger(__name__)

# Global model manager instance
_model_manager: Optional[ModelManager] = None

def set_model_manager(model_manager: ModelManager) -> None:
    """Set the global model manager instance for the chat router."""
    global _model_manager
    _model_manager = model_manager
    logger.info("Model manager set successfully for chat router")

def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    if _model_manager is None:
        raise HTTPException(status_code=500, detail="Model manager not initialized")
    return _model_manager

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
    conversation_id: Optional[str] = None  # Changed from required to optional with default None
    chat_history: Optional[List[ChatMessage]] = []
    user_profile: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    response: str
    model_used: str
    confidence_score: float
    usage_stats: Dict[str, Any]
    conversation_id: str

class ConversationListItem(BaseModel):
    conversation_id: str
    last_message: str
    last_updated: str
    message_count: int

class ConversationListResponse(BaseModel):
    conversations: List[ConversationListItem]

class MessageListItem(BaseModel):
    user_id: str
    timestamp: int
    conversation_id: str
    message_type: str
    content: str
    sources: List[Dict[str, Any]] = []
    tools: List[Dict[str, Any]] = []
    created_at: str

class ConversationHistoryResponse(BaseModel):
    messages: List[MessageListItem]

# Initialize agent (will be injected as dependency)
react_agent = None

def get_react_agent():
    """Dependency to get ReAct agent instance"""
    global react_agent
    if react_agent is None:
        try:
            react_agent = AgentService.create_agent()
        except Exception as e:
            logger.error(f"Failed to create ReAct agent: {str(e)}")
            raise HTTPException(status_code=503, detail="AI agent not available")
    return react_agent

def set_react_agent(agent):
    """Set the ReAct agent instance"""
    global react_agent
    react_agent = agent
    
# Legacy model manager for backward compatibility
model_manager = None

def get_model_manager() -> ModelManager:
    """Dependency to get model manager instance (legacy)"""
    global model_manager
    if model_manager is None:
        try:
            model_manager = ModelManager()
        except Exception as e:
            logger.error(f"Failed to get model manager: {str(e)}")
            raise HTTPException(status_code=503, detail="AI models not available")
    return model_manager

@chat_router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent = Depends(get_react_agent)
):
    """Main chat endpoint with chat history saving"""
    try:
        logger.info(f"Chat request received: {request.message[:50]}...")
        chat_history_service = ChatHistoryService()
        
        # Generate a conversation_id if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Save user message to chat history
        chat_history_service.save_user_message(
            user_id=str(current_user.id),
            message_content=request.message,
            conversation_id=conversation_id
        )
        
        # Process query using ReAct agent
        agent_response = await AgentService.process_query(
            agent=agent,
            query=request.message,
            user_id=str(current_user.id),
            conversation_id=conversation_id
        )
        
        logger.info(f"Chat response generated using ReAct agent")
        
        # Extract sources and tools from agent response
        sources = agent_response.sources if hasattr(agent_response, 'sources') else []
        tools_used = agent_response.tool_usage if hasattr(agent_response, 'tool_usage') else []
        
        # Save assistant response to chat history
        chat_history_service.save_assistant_message(
            user_id=str(current_user.id),
            message_content=agent_response.response,
            conversation_id=conversation_id,
            sources=sources,
            tools=tools_used
        )

        # Prepare usage stats
        usage_stats = {
            "sources": sources,
            "tools": tools_used,
            "reasoning": agent_response.reasoning if hasattr(agent_response, 'reasoning') else ""
        }

        return ChatResponse(
            response=agent_response.response,
            model_used="ReAct Agent",
            confidence_score=1.0,  # ReAct agent doesn't provide confidence score
            usage_stats=usage_stats,
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

@chat_router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent = Depends(get_react_agent)
):
    """Streaming chat endpoint using Server-Sent Events with chat history saving"""
    try:
        logger.info(f"Streaming chat request received: {request.message[:50]}...")
        chat_history_service = ChatHistoryService()
        
        # Generate a conversation_id if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Save user message to chat history
        chat_history_service.save_user_message(
            user_id=str(current_user.id),
            message_content=request.message,
            conversation_id=conversation_id
        )
        
        # Process query using ReAct agent (non-streaming for now)
        agent_response = await AgentService.process_query(
            agent=agent,
            query=request.message,
            user_id=str(current_user.id),
            conversation_id=conversation_id
        )
        
        logger.info(f"Chat response generated using ReAct agent")
        
        # Extract sources and tools from agent response
        sources = agent_response.sources if hasattr(agent_response, 'sources') else []
        tools_used = agent_response.tool_usage if hasattr(agent_response, 'tool_usage') else []
        
        # Save assistant response to chat history
        chat_history_service.save_assistant_message(
            user_id=str(current_user.id),
            message_content=agent_response.response,
            conversation_id=conversation_id,
            sources=sources,
            tools=tools_used
        )
        
        # Return a single chunk as a stream
        async def generate():
            yield f"data: {json.dumps({'content': agent_response.response, 'type': 'content', 'conversation_id': conversation_id})}\n\n"
            
            # If there are sources, send them as a separate event
            if sources:
                yield f"data: {json.dumps({'sources': sources, 'type': 'sources', 'conversation_id': conversation_id})}\n\n"
            
            # If there are tools used, send them as a separate event
            if tools_used:
                yield f"data: {json.dumps({'tools': tools_used, 'type': 'tools', 'conversation_id': conversation_id})}\n\n"
                
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id})}\n\n"
            
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
        
        # Store the full response for saving to history after stream completes
        full_response_chunks = []
        
        # Generate streaming response
        async def generate():
            try:
                async for chunk in model_manager.generate_streaming_response(
                    prompt=request.message,
                    context=context
                ):
                    # Add chunk to full response
                    if isinstance(chunk, str):
                        content = chunk
                    else:
                        content = chunk.get('content', '')
                    
                    full_response_chunks.append(content)
                    
                    # Format as SSE data
                    yield f"data: {json.dumps({'content': content, 'type': 'content', 'conversation_id': conversation_id})}\n\n"
                
                # Stream is complete, save the full response to chat history
                complete_response = "".join(full_response_chunks)
                chat_history_service.save_assistant_message(
                    user_id=str(current_user.id),
                    message_content=complete_response,
                    conversation_id=conversation_id,
                    sources=[],  # Add sources if available in your model response
                    tools=[]     # Add tools if available in your model response
                )
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id})}\n\n"
                logger.info(f"Completed streaming response and saved to history for conversation: {conversation_id}")
                
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

@chat_router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    limit: int = Query(default=10, description="Maximum number of conversations to retrieve"),
    offset: int = Query(default=0, description="Number of conversations to skip for pagination"),
    current_user: User = Depends(get_current_user)
):
    """Get the user's recent conversations."""
    try:
        chat_history_service = ChatHistoryService()
        conversations = chat_history_service.get_user_conversations(
            user_id=str(current_user.id),
            limit=limit,
            offset=offset
        )
        return ConversationListResponse(conversations=conversations)
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversations"
        )

@chat_router.get("/conversation/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the full history of a specific conversation."""
    try:
        chat_history_service = ChatHistoryService()
        messages = chat_history_service.get_conversation_history(
            user_id=str(current_user.id),
            conversation_id=conversation_id
        )
        return ConversationHistoryResponse(messages=messages)
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation history"
        )

@chat_router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an entire conversation."""
    try:
        chat_history_service = ChatHistoryService()
        success = chat_history_service.delete_conversation(
            user_id=str(current_user.id),
            conversation_id=conversation_id
        )
        if success:
            return {"message": "Conversation deleted successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete conversation"
            )
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation"
        )