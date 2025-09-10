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

# Import AI model components
from ai_models.model_factory import ModelFactory
from ai_models.model_manager import ModelManager

# Import database connections
from database.connections.rds_postgres import postgres_connection

# Import authentication components
from api.routes.auth import auth_router
from api.routes.chat import chat_router, set_model_manager
from api.routes.preferences import preferences_router
from api.middleware.auth_middleware import JWTBearerMiddleware

# Import transcription components
from api.routes.transcription_route import router as transcription_router

# Import web scraping components
from api.routes.web_scraping import router as web_scraping_router

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
    models: Dict[str, bool]
    message: str

# Initialize model manager
try:
    model_manager = ModelManager()
    logger.info("Model manager initialized successfully")
    set_model_manager(model_manager)
except Exception as e:
    logger.error(f"Failed to initialize model manager: {str(e)}")
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
        logger.error(f"Database health check failed: {str(e)}")
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
        logger.error(f"Health check failed: {str(e)}")
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

@app.get("/api/models")
async def list_models():
    """List available AI models"""
    if not model_manager:
        logger.error("Models endpoint called but model manager is not available")
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        logger.info("Listing available models")
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
        logger.error(f"Failed to list models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")
async def list_models():
    """List available AI models"""
    if not model_manager:
        logger.error("Models endpoint called but model manager is not available")
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    try:
        logger.info("Listing available models")
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
        logger.error(f"Failed to list models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

