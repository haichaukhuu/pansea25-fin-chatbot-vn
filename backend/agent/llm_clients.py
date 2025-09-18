import json
import os
import boto3
from typing import Dict, List, Any, Optional, Union
from langchain_core.language_models import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import Generation, LLMResult


class AWSBedrockLLM(LLM):
    """LangChain wrapper for AWS Bedrock models."""
    
    client: Any  # boto3 bedrock client
    model_id: str
    model_kwargs: Dict[str, Any] = {}
    streaming: bool = False
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "aws_bedrock"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the AWS Bedrock model."""
        # Prepare the request based on model type
        if "anthropic.claude" in self.model_id:
            return self._call_claude(prompt, stop, run_manager, **kwargs)
        elif "llama" in self.model_id.lower():
            return self._call_llama(prompt, stop, run_manager, **kwargs)
        else:
            raise ValueError(f"Unsupported model: {self.model_id}")
    
    def _call_claude(self, prompt: str, stop: Optional[List[str]] = None, 
                    run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> str:
        """Call Claude model on AWS Bedrock."""
        # Use the converse API for Claude models (required for Claude Sonnet)
        try:
            # Prepare messages for the conversation
            messages = [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
            
            # Configure inference parameters
            inference_config = {
                "maxTokens": self.model_kwargs.get("max_tokens", 1000),
                "temperature": self.model_kwargs.get("temperature", 0.7),
                "topP": 0.9
            }
            
            if stop:
                inference_config["stopSequences"] = stop
            
            # Make the API call using converse instead of invoke_model
            response = self.client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            
            # Extract the response text
            if response and "output" in response:
                message = response["output"]
                if "message" in message:
                    content = message.get("content", [])
                    if content and len(content) > 0:
                        for block in content:
                            if block.get("type") == "text":
                                return block.get("text", "")
            
            return ""
            
        except Exception as e:
            import logging
            logging.error(f"Error calling Claude model: {e}")
            # Fall back to invoke_model if converse isn't available (for older Claude models)
            try:
                # Claude-specific request format
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.model_kwargs.get("max_tokens", 1000),
                    "temperature": self.model_kwargs.get("temperature", 0.7),
                    "messages": [
                        {"role": "user", "content": [{"type": "text", "text": prompt}]}
                    ]
                }
                
                if stop:
                    request_body["stop_sequences"] = stop
                
                # Merge any additional kwargs
                request_body.update({k: v for k, v in kwargs.items() if k not in request_body})
                
                # Make the API call
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
                
                # Parse the response
                response_body = json.loads(response.get('body').read())
                # Bedrock Claude messages API returns content as a list with type/text
                content = response_body.get('content', [])
                if content and isinstance(content, list):
                    item = content[0]
                    if isinstance(item, dict):
                        return item.get('text', '') or item.get('content', '')
                return response_body.get('output_text', '') or ""
            except Exception as e:
                logging.error(f"Fallback invoke_model failed: {e}")
                raise
    
    def _call_llama(self, prompt: str, stop: Optional[List[str]] = None, 
                   run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> str:
        """Call Llama model on AWS Bedrock."""
        # Llama-specific request format
        request_body = {
            "prompt": prompt,
            "max_gen_len": self.model_kwargs.get("max_tokens", 1000),
            "temperature": self.model_kwargs.get("temperature", 0.7),
        }
        
        if stop:
            request_body["stop"] = stop
        
        # Merge any additional kwargs
        request_body.update({k: v for k, v in kwargs.items() if k not in request_body})
        
        # Make the API call
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        return response_body.get('generation')


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_bedrock_client():
        """Create a boto3 client for AWS Bedrock."""
        # Use AWS Bedrock-specific region
        from config import Config
        bedrock_region = os.environ.get('AWS_BEDROCK_REGION', 'us-east-1')
        
        # Create a session with region only
        # This will use the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from environment
        # Which should be set correctly via config.py setup
        session = boto3.Session(
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
            region_name=bedrock_region
        )
        
        # Create client from session with standard parameters
        client_kwargs = {
            'service_name': 'bedrock-runtime',
            'region_name': bedrock_region,
        }
        
        # For enhanced debugging
        import logging
        logging.getLogger('botocore').setLevel(logging.DEBUG)
        
        return session.client(**client_kwargs)
    
    @staticmethod
    def create_llm(model_name: str, temperature: float = 0.7, max_tokens: int = 1000) -> AWSBedrockLLM:
        """Create a generic Bedrock LLM client by model name/ID.
        
        If the model name contains 'anthropic' or 'claude', it will be routed to the Claude caller.
        If it contains 'llama', it will be routed to the Llama caller.
        
        Note: For Claude models, prefer using create_claude_llm() which respects environment configuration.
        """
        client = LLMClientFactory.create_bedrock_client()
        return AWSBedrockLLM(
            client=client,
            model_id=model_name,
            model_kwargs={
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
    
    @staticmethod
    def create_claude_llm(temperature: float = 0.7, max_tokens: int = 1000, model_id: Optional[str] = None) -> AWSBedrockLLM:
        """Create Claude Sonnet LLM client using the AWS Bedrock API.
        
        Uses the model specified in AWS_BEDROCK_CLAUDE_MODEL env var.
        For this application, we use anthropic.claude-sonnet-4-20250514-v1:0 exclusively."""
        client = LLMClientFactory.create_bedrock_client()
        # Use the model ID from environment config or default to the allowed model
        from config import Config
        model_id = model_id or Config.AWS_BEDROCK_CLAUDE_MODEL
        return AWSBedrockLLM(
            client=client,
            model_id=model_id,
            model_kwargs={
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
    
    @staticmethod
    def create_llama_llm(temperature: float = 0.7, max_tokens: int = 1000) -> AWSBedrockLLM:
        """Create Llama-SEA-LION-v3-8B-IT LLM client."""
        client = LLMClientFactory.create_bedrock_client()
        return AWSBedrockLLM(
            client=client,
            model_id="llama-sea-lion-v3-8b-it",  # This ID needs to be updated with the actual ID once deployed
            model_kwargs={
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )