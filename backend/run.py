#!/usr/bin/env python3
"""
Startup script for AgriFinHub Chatbot Backend
"""

import uvicorn
import sys
import os
from pathlib import Path
import time

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import validate_config, API_CONFIG, setup_logging

def main():
    """Main startup function"""
    # Set up logging first thing
    setup_logging()
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Starting AgriFinHub Chatbot Backend...")
    
    # Display startup information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Validate configuration
    logger.info("Validating configuration...")
    start_time = time.time()
    if not validate_config():
        logger.critical("Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    validation_time = time.time() - start_time
    logger.info(f"Configuration validated successfully ({validation_time:.2f}s)")
    logger.info(f"Server will start on {API_CONFIG['host']}:{API_CONFIG['port']}")
    
    try:
        logger.info("Starting uvicorn server...")
        uvicorn.run(
            "main:app",
            host=API_CONFIG["host"],
            port=API_CONFIG["port"],
            reload=API_CONFIG["debug"],
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
