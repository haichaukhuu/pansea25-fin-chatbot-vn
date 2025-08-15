#!/usr/bin/env python3
"""
Startup script for AgriFinHub Chatbot Backend
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import validate_config, API_CONFIG

def main():
    """Main startup function"""
    print("🚀 Starting AgriFinHub Chatbot Backend...")
    
    # Validate configuration
    if not validate_config():
        print("❌ Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    print("✅ Configuration validated successfully")
    print(f"🌐 Server will start on {API_CONFIG['host']}:{API_CONFIG['port']}")
    print("🔑 Using Gemma 3N 8B IT model via Google AI Studio")
    
    try:
        uvicorn.run(
            "main:app",
            host=API_CONFIG["host"],
            port=API_CONFIG["port"],
            reload=API_CONFIG["debug"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
