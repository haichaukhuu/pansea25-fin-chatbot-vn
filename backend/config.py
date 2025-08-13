import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model configurations
MODEL_CONFIGS = {
    "gemma": {
        "name": "Gemma 3 27B IT",
        "model_id": "gemma-3-27b-it",
        "temperature": 0.7,
        "max_tokens": 4096,
        "is_primary": True,
        "capabilities": ["chat", "text_generation"],
        "provider": "google_genai"
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
        "http://127.0.0.1:3000"
    ]
}

# AI Model Configuration
AI_CONFIG = {
    "default_model": "gemma",
    "api_key": os.getenv("GOOGLE_GENAI_API_KEY"),
    "fallback_models": [],
    "max_retries": 3,
    "timeout": 30
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

def get_config() -> Dict[str, Any]:
    """Get all configuration"""
    return {
        "models": MODEL_CONFIGS,
        "api": API_CONFIG,
        "ai": AI_CONFIG,
        "logging": LOGGING_CONFIG,
        "chat": CHAT_CONFIG
    }

def validate_config() -> bool:
    """Validate that required configuration is present"""
    if not AI_CONFIG["api_key"]:
        print("ERROR: GOOGLE_GENAI_API_KEY environment variable is required")
        return False
    
    if not MODEL_CONFIGS:
        print("ERROR: No model configurations found")
        return False
    
    return True
