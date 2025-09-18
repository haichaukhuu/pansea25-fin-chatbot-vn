"""
Embeddings Factory Module
This module provides factory methods for creating embeddings models
"""

import logging
from typing import Optional, Dict, Any, List
from langchain_core.embeddings import Embeddings
from config import Config

logger = logging.getLogger(__name__)

def create_embeddings_model(
    model_type: str = "bedrock",
    model_name: str = "amazon.titan-embed-text-v2:0",
    **kwargs
) -> Embeddings:
    """Factory method to create embeddings model.
    
    Args:
        model_type: Type of embedding model (bedrock)
        model_name: The name or ID of the model
        **kwargs: Additional arguments to pass to the model
        
    Returns:
        An Embeddings instance
    """
    if model_type.lower() == "bedrock":
        try:
            from agent.tools.bedrock_embeddings import BedrockEmbeddings
            
            model_id = model_name or "amazon.titan-embed-text-v2:0"
            region_name = Config.AWS_BEDROCK_REGION or kwargs.get("region_name", "us-east-1")
            logger.info(f"Creating AWS Bedrock embeddings model: {model_id}")
            
            return BedrockEmbeddings(
                model_id=model_id,
                region_name=region_name
            )
        except ImportError:
            logger.error("Failed to import BedrockEmbeddings. Check AWS dependencies.")
            raise
        except Exception as e:
            logger.error(f"Failed to create AWS Bedrock embeddings model: {str(e)}")
            raise
    
    else:
        logger.warning(f"Unsupported embeddings model type: {model_type}. Using Bedrock embeddings as default.")
        return create_embeddings_model(model_type="bedrock", model_name="amazon.titan-embed-text-v2:0", **kwargs)