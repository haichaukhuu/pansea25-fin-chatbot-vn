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
        # Claude-specific request format
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.model_kwargs.get("max_tokens", 1000),
            "temperature": self.model_kwargs.get("temperature", 0.7),
            "messages": [
                {"role": "user", "content": prompt}
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
        return response_body.get('content')[0].get('text')
    
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
        # Use AWS credentials from environment variables or IAM role
        return boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
    
    @staticmethod
    def create_claude_llm(temperature: float = 0.7, max_tokens: int = 1000) -> AWSBedrockLLM:
        """Create Claude Sonnet 4 LLM client."""
        client = LLMClientFactory.create_bedrock_client()
        return AWSBedrockLLM(
            client=client,
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
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