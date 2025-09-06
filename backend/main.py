from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config import API_CONFIG

# Import AI model components
from ai_models.model_factory import ModelFactory
from ai_models.model_manager import ModelManager

# Import database connections
from database.connections.rds_postgres import postgres_connection

# Import authentication components
from auth.routes import auth_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AgriFinHub Chatbot API",
    description="AI-powered financial assistant for smallholder farmers in Vietnam",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and AI models on startup"""
    try:
        # Initialize PostgreSQL connection
        postgres_connection.initialize()
        
        # Create database tables if they don't exist
        postgres_connection.create_tables()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

# Include authentication router
app.include_router(auth_router, prefix="/api")

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

class HealthResponse(BaseModel):
    status: str
    models: Dict[str, bool]
    message: str

# Initialize model manager
try:
    model_manager = ModelManager()
    logger.info("Model manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize model manager: {e}")
    model_manager = None

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "AgriFinHub Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_status = "healthy"
    model_status = {}
    
    # Check database health
    try:
        with postgres_connection.get_db_session() as db:
            # Simple query to check DB connection
            pass
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check model health
    if not model_manager:
        return HealthResponse(
            status="degraded" if db_status == "healthy" else "unhealthy",
            models={},
            message="Model manager not initialized, database status: " + db_status
        )
    
    try:
        available_models = model_manager.get_available_models()
        if not available_models:
            return HealthResponse(
                status="degraded" if db_status == "healthy" else "unhealthy",
                models={},
                message="No models available, database status: " + db_status
            )
        
        for model_name in available_models:
            is_healthy = await model_manager.check_model_health(model_name)
            model_status[model_name] = is_healthy
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        model_status = {"error": False}
    
    # Overall status is healthy only if both database and all models are healthy
    overall_status = "healthy" if db_status == "healthy" and all(model_status.values()) else "degraded"
    if db_status == "unhealthy" and not all(model_status.values()):
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        models=model_status,
        message=f"API is running, database status: {db_status}"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="AI models not available")
    
    # Check if any models are available
    available_models = model_manager.get_available_models()
    if not available_models:
        raise HTTPException(status_code=503, detail="No AI models available")
    
    try:
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
        
        return ChatResponse(
            response=response.content,
            model_used=response.model_used,
            confidence_score=response.confidence_score,
            usage_stats=response.usage_stats
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="AI models not available")
    
    try:
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
                
            except Exception as e:
                logger.error(f"Streaming generation error: {e}")
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
        logger.error(f"Streaming chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate streaming response: {str(e)}")

@app.get("/models")
async def list_models():
    """List available AI models"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        models = model_manager.get_available_models()
        model_info = {}
        
        for model_name in models:
            model = model_manager.get_model(model_name)
            if model:
                model_info[model_name] = {
                    "name": model.config.name,
                    "model_id": model.config.model_id,
                    "is_available": model.is_available,
                    "capabilities": [cap.value for cap in model.config.capabilities]
                }
        
        return {"models": model_info}
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
