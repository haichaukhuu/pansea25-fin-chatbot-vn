from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import logging

# Import config
from config import Config, API_CONFIG, setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Import agent components (new implementation)
from agent.agent_service import AgentService

# Import database connections
from database.connections.rds_postgres import postgres_connection

# Import routers that use the new agent system
from api.routes.auth import auth_router
from api.routes.chat import chat_router  # Uses AgentService internally
from api.routes.preferences_route import preferences_router
from api.middleware.auth_middleware import JWTBearerMiddleware

# Import transcription components
from api.routes.transcription_route import router as transcription_router


# Import web scraping components
from api.routes.web_scraping import router as web_scraping_router
# Import weather service components
from api.routes.weather import weather_router


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

# Include routers
app.include_router(auth_router, prefix="/api")  
app.include_router(chat_router)
app.include_router(preferences_router, prefix="/api")

app.include_router(web_scraping_router)

app.include_router(weather_router, prefix="/api")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and AI models on startup"""
    try:
        logger.info("Starting AgriFinHub Chatbot API")
        
        # Initialize PostgreSQL connection
        postgres_connection.initialize()
        
        # Create database tables if they don't exist
        postgres_connection.create_tables()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {str(e)}")
        raise

# Include transcription router
app.include_router(transcription_router)

# Security
security = HTTPBearer()

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    agent_status: Dict[str, bool]
    message: str

# Initialize agent service
try:
    # Test agent creation to ensure it works
    test_agent = AgentService.create_agent()
    logger.info("Agent service initialized successfully")
    agent_available = True
except Exception as e:
    logger.error(f"Failed to initialize agent service: {str(e)}")
    agent_available = False

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
    agent_status = {}
    
    # Check database health
    try:
        with postgres_connection.get_db_session() as db:
            # Simple query to check DB connection
            pass
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    # Check agent health
    if not agent_available:
        return HealthResponse(
            status="degraded" if db_status == "healthy" else "unhealthy",
            agent_status={"agent_service": False},
            message="Agent service not initialized, database status: " + db_status
        )
    
    try:
        # Test agent creation
        test_agent = AgentService.create_agent()
        agent_status["agent_service"] = True
        agent_status["claude_sonnet"] = True  # Claude for tool execution
        agent_status["sealion_chat"] = True   # SEA-LION for chat
        agent_status["llama4_fallback"] = True  # Llama4 for fallback
    except Exception as e:
        logger.error(f"Agent health check failed: {str(e)}")
        agent_status = {"agent_service": False}
    
    # Overall status is healthy only if both database and agent are healthy
    overall_status = "healthy" if db_status == "healthy" and all(agent_status.values()) else "degraded"
    if db_status == "unhealthy" and not all(agent_status.values()):
        overall_status = "unhealthy"
   
    return HealthResponse(
        status=overall_status,
        agent_status=agent_status,
        message=f"API is running, database status: {db_status}"
    )

@app.get("/api/models")
async def list_models():
    """List available AI models/agents"""
    if not agent_available:
        logger.error("Models endpoint called but agent service is not available")
        raise HTTPException(status_code=503, detail="Agent service not available")
    
    try:
        logger.info("Listing available agent models")
        
        # Return information about our agent architecture
        model_info = {
            "claude_sonnet_4": {
                "name": "Claude Sonnet 4",
                "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
                "role": "Tool execution and ReAct reasoning",
                "is_available": agent_available,
                "capabilities": ["tool_calling", "reasoning", "analysis"]
            },
            "sealion": {
                "name": "SEA-LION",
                "model_id": "arn:aws:bedrock:us-east-1:184208908322:imported-model/za0nlconhflh",
                "role": "Primary Vietnamese chat model",
                "is_available": agent_available,
                "capabilities": ["vietnamese_chat", "conversation", "responses"]
            },
            "llama4_maverick": {
                "name": "Llama4 Maverick",
                "model_id": "us.meta.llama4-maverick-17b-instruct-v1:0",
                "role": "Fallback Vietnamese chat model",
                "is_available": agent_available,
                "capabilities": ["vietnamese_chat", "conversation", "fallback"]
            }
        }
        
        return {"models": model_info}
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

