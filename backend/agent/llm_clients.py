import json
import os
import logging
from typing import Dict, List, Any, Optional, Union

try:
    import boto3
    from botocore.config import Config
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Import LangChain AWS Bedrock integration
try:
    from langchain_aws import ChatBedrock, BedrockLLM
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Import direct Bedrock client for imported models
try:
    from .bedrock_direct_client import SEALionClient, BedrockDirectClient
    DIRECT_CLIENT_AVAILABLE = True
except ImportError:
    DIRECT_CLIENT_AVAILABLE = False

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_aws_bedrock_config

logger = logging.getLogger(__name__)

class LLMClientFactory:
    """Factory for creating LLM clients using LangChain AWS integration and direct boto3 clients."""
    
    @staticmethod
    def create_bedrock_session():
        """Create a boto3 session for AWS Bedrock with proper credentials."""
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required but not available. Please install with: pip install boto3")
        
        bedrock_config = get_aws_bedrock_config()
        session = boto3.Session(
            aws_access_key_id=bedrock_config["access_key_id"],
            aws_secret_access_key=bedrock_config["secret_access_key"],
            region_name=bedrock_config["region"]
        )
        return session
    
    @staticmethod
    def create_claude_chat_model(
        temperature: float = 0.2, 
        max_tokens: int = 50000,  
        model_id: Optional[str] = None
    ):
        """
        Create Claude Sonnet 4 chat model using ChatBedrock for proper streaming support.
        
        Args:
            temperature: Temperature for generation (0.0 to 1.0) - lower for reasoning tasks
            max_tokens: Maximum tokens to generate
            model_id: Override the default Claude model ID
            
        Returns:
            ChatBedrock instance configured for Claude Sonnet 4
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain-aws is required but not available. Please install with: pip install langchain-aws")
        
        bedrock_config = get_aws_bedrock_config()
        
        # Use inference profile ID for Claude Sonnet 4 (not direct model ID)
        model_id = model_id or "us.anthropic.claude-sonnet-4-20250514-v1:0"  # US inference profile
        
        logger.info(f"Creating Claude chat model with inference profile ID: {model_id}")
        
        # Create retry configuration to handle throttling
        retry_config = None
        if BOTO3_AVAILABLE:
            retry_config = Config(
                retries={
                    'total_max_attempts': 50,  # Increased from default 5 to 50
                    'mode': 'standard'  # Use standard retry mode for better throttling handling
                }
            )
        
        return ChatBedrock(
            model=model_id,
            aws_access_key_id=bedrock_config["access_key_id"],
            aws_secret_access_key=bedrock_config["secret_access_key"],
            region_name=bedrock_config["region"],
            model_kwargs={
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            config=retry_config,  # Add retry configuration for throttling
            beta_use_converse_api=True  # Use modern Converse API for better streaming
            # Note: streaming is handled by LangGraph automatically, don't pass it here
        )
    
    @staticmethod
    def create_sealion_direct_client(
        temperature: float = 0.3, 
        max_tokens: int = 50000  
    ):
        """
        Create SEA-LION direct client using boto3 for imported models.
        
        This method creates a direct boto3 client for the SEA-LION imported model
        which requires InvokeModel and InvokeModelWithResponseStream calls.
        
        Args:
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            SEALionClient instance configured for direct API calls
        """
        if not DIRECT_CLIENT_AVAILABLE:
            raise ImportError("Direct Bedrock client not available. Please check bedrock_direct_client.py")
        
        bedrock_config = get_aws_bedrock_config()
        
        logger.info("Creating SEA-LION direct client for imported model")
        
        # First create the BedrockDirectClient
        bedrock_direct_client = BedrockDirectClient(
            aws_access_key_id=bedrock_config["access_key_id"],
            aws_secret_access_key=bedrock_config["secret_access_key"],
            region_name=bedrock_config["region"],
            model_id=bedrock_config.get("sealion_model_id", "arn:aws:bedrock:us-east-1:184208908322:imported-model/za0nlconhflh")
        )
        
        # Then create the SEALionClient with the BedrockDirectClient
        return SEALionClient(bedrock_direct_client)
    
    @staticmethod
    def create_sealion_llm(
        temperature: float = 0.3, 
        max_tokens: int = 50000,  
        model_id: Optional[str] = None,
        use_direct_client: bool = True
    ):
        """
        Create SEA-LION LLM model.
        
        Args:
            temperature: Temperature for generation (0.0 to 1.0) - lower for more focused responses
            max_tokens: Maximum tokens to generate
            model_id: Override the default SEA-LION model ID (custom import ID)
            use_direct_client: If True, use direct boto3 client (recommended for imported models)
            
        Returns:
            SEALionClient or BedrockLLM instance configured for SEA-LION
        """
        if use_direct_client:
            # Use direct boto3 client for imported models (recommended)
            return LLMClientFactory.create_sealion_direct_client(temperature, max_tokens)
        else:
            # Fallback to LangChain BedrockLLM (may not work with imported models)
            if not LANGCHAIN_AVAILABLE:
                raise ImportError("langchain-aws is required for BedrockLLM but not available")
            
            bedrock_config = get_aws_bedrock_config()
            
            # Use provided model_id or default from config
            model_id = model_id or bedrock_config["sealion_model"]
            
            logger.info(f"Creating SEA-LION LLM with model ID: {model_id}")
            
            # Create retry configuration to handle throttling
            retry_config = None
            if BOTO3_AVAILABLE:
                retry_config = Config(
                    retries={
                        'total_max_attempts': 50,  # Increased from default 5 to 50
                        'mode': 'standard'  # Use standard retry mode for better throttling handling
                    }
                )
            
            return BedrockLLM(
                model_id=model_id,
                aws_access_key_id=bedrock_config["access_key_id"],
                aws_secret_access_key=bedrock_config["secret_access_key"],
                region_name=bedrock_config["region"],
                streaming=True,  # Enable streaming for async operations
                model_kwargs={
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                config=retry_config  # Add retry configuration for throttling
            )
    
    @staticmethod
    def create_llama4_maverick_llm(
        temperature: float = 0.4, 
        max_tokens: int = 50000,  
        model_id: Optional[str] = None
    ):
        """
        Create Llama4 Maverick chat model as fallback for user conversations.
        
        This model serves as a fallback when SEA-LION is unavailable, ensuring that
        Claude never becomes the chat model. Llama4 Maverick can handle Vietnamese
        conversations reasonably well as a backup option.
        
        Args:
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            model_id: Override the default Llama4 Maverick model ID
            
        Returns:
            ChatBedrock instance configured for Llama4 Maverick
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain-aws is required but not available")
        
        bedrock_config = get_aws_bedrock_config()
        
        # Use provided model_id or default
        model_id = model_id or "us.meta.llama4-maverick-17b-instruct-v1:0"
        
        logger.info(f"Creating Llama4 Maverick chat model with model ID: {model_id}")
        
        # Create retry configuration to handle throttling
        retry_config = None
        if BOTO3_AVAILABLE:
            retry_config = Config(
                retries={
                    'total_max_attempts': 50,
                    'mode': 'standard'
                }
            )
        
        return ChatBedrock(
            model_id=model_id,
            aws_access_key_id=bedrock_config["access_key_id"],
            aws_secret_access_key=bedrock_config["secret_access_key"],
            region_name=bedrock_config["region"],
            model_kwargs={
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            config=retry_config,
            beta_use_converse_api=True  # Use modern Converse API for better streaming
        )
    
    @staticmethod
    def create_llm(model_name: str, temperature: float = 0.7, max_tokens: int = 50000):  
        """
        Create a generic Bedrock LLM client by model name/ID.
        
        Args:
            model_name: Model name or ID
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Appropriate LangChain model instance or direct client
        """
        if "anthropic.claude" in model_name or "claude" in model_name.lower():
            return LLMClientFactory.create_claude_chat_model(temperature, max_tokens, model_name)
        elif "sealion" in model_name.lower() or "za0nlconhflh" in model_name:
            return LLMClientFactory.create_sealion_llm(temperature, max_tokens, model_name)
        elif "llama4-maverick" in model_name.lower() or "maverick" in model_name.lower():
            return LLMClientFactory.create_llama4_maverick_llm(temperature, max_tokens, model_name)
        else:
            # Default to Claude for unknown models
            return LLMClientFactory.create_claude_chat_model(temperature, max_tokens, model_name)
    
    @staticmethod
    def create_claude_llm(temperature: float = 0.2, max_tokens: int = 50000, model_id: Optional[str] = None):
        """
        Create Claude Sonnet 4 LLM client using ChatBedrock.
        This is the preferred method for Claude models due to better streaming support.
        
        Args:
            temperature: Temperature for generation (lower for reasoning tasks)
            max_tokens: Maximum tokens to generate
            model_id: Override the default Claude model
            
        Returns:
            ChatBedrock instance
        """
        return LLMClientFactory.create_claude_chat_model(temperature, max_tokens, model_id)
    
    @staticmethod
    def create_llama_llm(temperature: float = 0.3, max_tokens: int = 50000):
        """
        Create SEA-LION LLM client for Vietnamese response generation.
        
        Note: This method name is legacy - it actually creates SEA-LION, not Llama.
        Maintained for backward compatibility.
        
        Args:
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            SEALionClient instance (direct boto3 client for imported models)
        """
        return LLMClientFactory.create_sealion_llm(temperature, max_tokens)