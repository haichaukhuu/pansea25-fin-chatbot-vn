import os
import json
import boto3
import numpy as np
from typing import List, Dict, Any, Optional


class BedrockEmbeddings:
    """
    AWS Bedrock Titan Text Embeddings for use with LangChain
    """

    def __init__(self, model_id: str = "amazon.titan-embed-text-v2:0", region_name: Optional[str] = None):
        """
        Initialize the Bedrock embeddings client
        
        Args:
            model_id: The AWS Bedrock model ID
            region_name: AWS region name (defaults to AWS_BEDROCK_REGION env var or us-east-1)
        """
        self.model_id = model_id
        self.region_name = region_name or os.environ.get("AWS_BEDROCK_REGION", "us-east-1")
        
        # Initialize Bedrock client using AWS_BEDROCK API key
        # The AWS_BEDROCK_API_KEY should be used for authentication, not transcribe keys
        bedrock_api_key = os.environ.get("AWS_BEDROCK_API_KEY")
        
        # Initialize session with region only - will use default credentials from env
        session = boto3.Session(region_name=self.region_name)
        
        # Create client from session - will use AWS SDK's default credential provider chain
        # which is separate from Transcribe credentials
        self.client = session.client('bedrock-runtime')
        
        # For compatibility with LangChain
        self.embedding_dimension = 1536

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents
        
        Args:
            texts: List of documents to embed
            
        Returns:
            List of embeddings, one for each document
        """
        return [self.embed_query(text) for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query text
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        # Prepare request payload
        request_body = {
            "inputText": text
        }
        
        # Make the API call
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        embedding = response_body.get('embedding', [])
        
        return embedding