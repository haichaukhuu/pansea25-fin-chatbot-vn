"""
Direct AWS Bedrock Client for Imported Models

This module provides direct boto3 integration for AWS Bedrock imported models
that require InvokeModel and InvokeModelWithResponseStream calls instead of
standard LangChain integrations.

Specifically designed for SEA-LION imported model:
ModelID: arn:aws:bedrock:us-east-1:184208908322:imported-model/za0nlconhflh
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Iterator
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not available. Please install with: pip install boto3")


class BedrockDirectClient:
    """
    Direct AWS Bedrock client for imported models using boto3 InvokeModel calls.
    
    This client is specifically designed for imported models that cannot use
    standard LangChain Bedrock integrations and require direct API calls.
    """
    
    def __init__(
        self, 
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str = "us-east-1",
        model_id: str = None
    ):
        """
        Initialize the direct Bedrock client.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key  
            region_name: AWS region (default: us-east-1)
            model_id: Bedrock model ID (can be overridden per call)
        """
        self.model_id = model_id
        
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required but not installed. Please install with: pip install boto3")
        
        # Configure client with retry settings
        config = Config(
            region_name=region_name,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=50
        )
        
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                config=config
            )
            logger.info(f"Bedrock direct client initialized for region: {region_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    def invoke(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 2000,
        model_id: str = None
    ) -> str:
        """
        Invoke the model with a prompt and return the response.
        
        Args:
            prompt: Input prompt for the model
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            model_id: Model ID to use (overrides instance default)
            
        Returns:
            Generated text response
        """
        target_model_id = model_id or self.model_id
        if not target_model_id:
            raise ValueError("No model_id provided either in constructor or method call")
        
        # Prepare the payload for SEA-LION with improved parameters to prevent hashtag spam
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "top_p": 0.8,  # Lower top_p for more focused responses
            "top_k": 40,   # Add top_k for better quality
            "repetition_penalty": 1.1,  # Prevent repetitive hashtags
            "do_sample": True
        }
        
        try:
            logger.debug(f"Invoking model {target_model_id} with prompt length: {len(prompt)}")
            
            response = self.client.invoke_model(
                modelId=target_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            
            response_body = json.loads(response['body'].read())
            logger.debug(f"Model response format: {response_body}")
            
            # Extract the generated text from response
            # SEA-LION response format: {"generation": "...", "stop_reason": "...", ...}
            if "generation" in response_body:
                generation = response_body["generation"]
                stop_reason = response_body.get("stop_reason", "unknown")
                
                # Remove the original prompt from the response if it's included
                if generation.startswith(prompt):
                    generation = generation[len(prompt):].strip()

                # Check for quality issues
                if stop_reason == "length":
                    logger.warning(f"Model hit token limit. Response may be truncated. Stop reason: {stop_reason}")
                
                # Check if response is mostly hashtags (poor quality indicator)
                hashtag_ratio = generation.count('#') / max(len(generation), 1)
                if hashtag_ratio > 0.1:  # More than 10% hashtags indicates poor output
                    logger.warning(f"Response contains excessive hashtags ({hashtag_ratio:.2%}), may indicate poor generation")
                    # Try to extract meaningful content before hashtags
                    hashtag_start = generation.find('#')
                    if hashtag_start > 50:  # If there's substantial content before hashtags
                        generation = generation[:hashtag_start].strip()
                        logger.info("Extracted content before hashtag spam")
                
                logger.debug(f"Model response length: {len(generation)}, stop_reason: {stop_reason}")
                return generation
            else:
                logger.error(f"Unexpected response format: {response_body}")
                return "Error: Unexpected response format from model"
                
        except ClientError as e:
            logger.error(f"AWS Bedrock API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error invoking model: {e}")
            raise
    
    async def ainvoke(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 2000,
        model_id: str = None
    ) -> str:
        """
        Asynchronously invoke the model with a prompt.
        
        Args:
            prompt: Input prompt for the model
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            model_id: Model ID to use (overrides instance default)
            
        Returns:
            Generated text response
        """
        # Run the synchronous call in a thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, 
                self.invoke, 
                prompt, 
                temperature, 
                max_tokens, 
                model_id
            )
    
    def stream(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 2000,
        model_id: str = None
    ) -> Iterator[str]:
        """
        Stream the model response in real-time.
        
        Args:
            prompt: Input prompt for the model
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            model_id: Model ID to use (overrides instance default)
            
        Yields:
            Chunks of generated text as they are produced
        """
        target_model_id = model_id or self.model_id
        if not target_model_id:
            raise ValueError("No model_id provided either in constructor or method call")
        
        # Prepare the payload for SEA-LION
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "top_p": 0.9
        }
        
        try:
            logger.debug(f"Streaming from model {target_model_id} with prompt length: {len(prompt)}")
            
            response = self.client.invoke_model_with_response_stream(
                modelId=target_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            
            # Process the streaming response
            for event in response['body']:
                if 'chunk' in event:
                    chunk_raw = event['chunk']['bytes']
                    chunk_data = json.loads(chunk_raw)
                    
                    # SEA-LION streaming format: {"bytes": "base64_encoded_data", "p": "..."}
                    if 'bytes' in chunk_data:
                        import base64
                        decoded_bytes = base64.b64decode(chunk_data['bytes'])
                        decoded_data = json.loads(decoded_bytes)
                        
                        if 'generation' in decoded_data:
                            chunk_text = decoded_data['generation']
                            if chunk_text:  # Only yield non-empty chunks
                                yield chunk_text
                            
        except ClientError as e:
            logger.error(f"AWS Bedrock streaming API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            raise
    
    async def astream(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 2000,
        model_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously stream the model response.
        
        Args:
            prompt: Input prompt for the model
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            model_id: Model ID to use (overrides instance default)
            
        Yields:
            Chunks of generated text as they are produced
        """
        # Run the synchronous streaming in a thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            future = loop.run_in_executor(
                executor, 
                lambda: list(self.stream(prompt, temperature, max_tokens, model_id))
            )
            chunks = await future
            for chunk in chunks:
                yield chunk


class SEALionClient:
    """
    Specialized client for SEA-LION model with Vietnamese response generation.
    """
    
    def __init__(self, bedrock_client: BedrockDirectClient):
        """
        Initialize SEA-LION client.
        
        Args:
            bedrock_client: Configured BedrockDirectClient instance
        """
        self.client = bedrock_client
    
    def generate_response(
        self, 
        user_query: str, 
        claude_analysis: str, 
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate a Vietnamese response based on user query and Claude's analysis.
        
        Args:
            user_query: Original user question
            claude_analysis: Claude's reasoning and analysis
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Vietnamese response text
        """
        prompt = f"""Bạn là chuyên gia tư vấn nông nghiệp và tài chính cho nông dân Việt Nam. Hãy trả lời câu hỏi dưới đây một cách chính xác và hữu ích.

Câu hỏi: {user_query}

Thông tin tham khảo: {claude_analysis}

Yêu cầu câu trả lời:
- Sử dụng tiếng Việt dễ hiểu
- Đưa ra lời khuyên thực tế và cụ thể
- Tập trung vào nội dung chính, không sử dụng hashtag
- Câu trả lời ngắn gọn, từ 50-200 từ

"""

        return self.client.invoke(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def agenerate_response(
        self, 
        user_query: str, 
        claude_analysis: str, 
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate a Vietnamese response asynchronously.
        
        Args:
            user_query: Original user question
            claude_analysis: Claude's reasoning and analysis
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Vietnamese response text
        """
        prompt = f"""Bạn là chuyên gia tư vấn nông nghiệp và tài chính cho nông dân Việt Nam. Hãy trả lời câu hỏi dưới đây một cách chính xác và hữu ích.

Câu hỏi: {user_query}

Thông tin tham khảo: {claude_analysis}

Yêu cầu câu trả lời:
- Sử dụng tiếng Việt dễ hiểu
- Đưa ra lời khuyên thực tế và cụ thể
- Tập trung vào nội dung chính, không sử dụng hashtag
- Câu trả lời ngắn gọn, từ 50-200 từ

"""

        return await self.client.ainvoke(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def stream_response(
        self, 
        user_query: str, 
        claude_analysis: str, 
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        Stream a Vietnamese response in real-time.
        
        Args:
            user_query: Original user question
            claude_analysis: Claude's reasoning and analysis
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of Vietnamese response text as they are generated
        """
        prompt = f"""Bạn là chuyên gia tư vấn nông nghiệp và tài chính cho nông dân Việt Nam. Hãy trả lời câu hỏi dưới đây một cách chính xác và hữu ích.

Câu hỏi: {user_query}

Thông tin tham khảo: {claude_analysis}

Yêu cầu câu trả lời:
- Sử dụng tiếng Việt dễ hiểu
- Đưa ra lời khuyên thực tế và cụ thể
- Tập trung vào nội dung chính, không sử dụng hashtag
- Câu trả lời ngắn gọn, từ 50-200 từ

"""

        async for chunk in self.client.astream(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield chunk