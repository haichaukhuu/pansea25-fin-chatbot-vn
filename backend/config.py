import os
from typing import Dict, Any, List
from dotenv import load_dotenv
import logging
import sys


# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Application settings
    APP_NAME = os.getenv("APP_NAME", "AgriFinHub")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # JWT Authentication settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_insecure_key_please_change")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Database settings
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    RDS_DATABASE_URL = os.getenv("RDS_DATABASE_URL")
    
    # AI Model settings
    GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
    
    # AWS settings
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

# Model configurations
MODEL_CONFIGS = {
    "gemini_flash": {
        "name": "Gemini 2.5 Flash",
        "model_id": "gemini-2.5-flash",
        "temperature": 0.7,
        "max_tokens": 4096,
        "is_primary": True,
        "capabilities": ["chat", "text_generation", "streaming", "multimodal"],
        "provider": "google_genai",
        "model_type": "gemini",
        "streaming_config": {
            "chunk_size": "medium",
            "optimization": "native_streaming"
        }
    },
    "gemini_pro": {
        "name": "Gemini 2.5 Pro",
        "model_id": "gemini-2.5-pro",
        "temperature": 0.6,
        "max_tokens": 8192,
        "is_primary": False,
        "capabilities": ["chat", "text_generation", "streaming", "multimodal", "reasoning"],
        "provider": "google_genai",
        "model_type": "gemini",
        "streaming_config": {
            "chunk_size": "large",
            "optimization": "native_streaming"
        }
    }
}

# API Configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "cors_origins": [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:3000",
        "https://agrifinhub.netlify.app"
    ]
}

# AI Model Configuration
AI_CONFIG = {
    "default_model": "gemini_flash",
    "api_key": os.getenv("GOOGLE_GENAI_API_KEY"),
    "fallback_models": ["gemini_pro"],
    "max_retries": 3,
    "timeout": 60,
    "streaming_config": {
        "enable_adaptive_streaming": True,
        "buffer_size": 1024,
        "chunk_timeout": 5.0,
        "enable_compression": True
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "stream": sys.stdout
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": True
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        },
        "sqlalchemy.engine": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False
        }
    }
}

# Chat Configuration
CHAT_CONFIG = {
    "max_history_length": 10,
    "max_message_length": 1000,
    "system_prompt": """Bạn là một cố vấn tài chính AI chuyên biệt cho nông dân nhỏ lẻ Việt Nam.

Trách nhiệm của bạn:
1. Cung cấp lời khuyên tài chính chính xác và phù hợp văn hóa
2. Giải thích các khái niệm tài chính bằng tiếng Việt đơn giản
3. Hướng dẫn người dùng về các chương trình vay nông nghiệp
4. Cảnh báo về các trò lừa đảo tài chính
5. Luôn ưu tiên sự an toàn và lợi ích tài chính của nông dân

Trả lời bằng tiếng Việt, thân thiện và dễ hiểu."""
}

# LangChain Configuration
LANGCHAIN_CONFIG = {
    "use_memory": True,
    "memory_window_size": 5,
    "embedding_model": "all-MiniLM-L6-v2",
    "vector_store": "faiss",
    "chunk_size": 1000,
    "chunk_overlap": 200
}

def get_config() -> Dict[str, Any]:
    """Get all configuration"""
    return {
        "models": MODEL_CONFIGS,
        "api": API_CONFIG,
        "ai": AI_CONFIG,
        "logging": LOGGING_CONFIG,
        "chat": CHAT_CONFIG,
        "langchain": LANGCHAIN_CONFIG
    }

def setup_logging():
    """Set up logging configuration"""
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")

def validate_config() -> bool:
    """Validate that required configuration is present"""
    errors: List[str] = []
    
    # Check JWT secret
    if not Config.JWT_SECRET_KEY or Config.JWT_SECRET_KEY == "default_insecure_key_please_change":
        errors.append("JWT_SECRET_KEY is missing or using default (insecure) value")
    
    # Check Google GenAI API key
    if not Config.GOOGLE_GENAI_API_KEY:
        errors.append("GOOGLE_GENAI_API_KEY is missing")
    
    # Check Database URL
    if not Config.RDS_DATABASE_URL:
        errors.append("RDS_DATABASE_URL is missing")
    
    # Check AWS credentials if needed
    if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
        errors.append("AWS credentials are missing")
    
    # Report errors
    if errors:
        print("ERROR: Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True
