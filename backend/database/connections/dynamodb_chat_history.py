import boto3
import os
import logging
from botocore.exceptions import ClientError
from config import get_aws_chat_history_config

logger = logging.getLogger(__name__)

class DynamoDBChatHistoryConnection:
    """Manages connections to DynamoDB for chat history storage."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to reuse the same connection."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the DynamoDB client with credentials."""
        try:
            # Get configuration from config.py
            config = get_aws_chat_history_config()
            
            # Using specific chat history AWS credentials from environment variables
            self.client = boto3.client(
                'dynamodb',
                aws_access_key_id=config['access_key_id'],
                aws_secret_access_key=config['secret_access_key'],
                region_name=config['region']
            )
            self.table_name = config['table_name']
            logger.info(f"DynamoDB chat history connection initialized for table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB chat history connection: {str(e)}")
            raise
    
    def get_client(self):
        """Returns the DynamoDB client."""
        return self.client
    
    def get_table_name(self):
        """Returns the DynamoDB table name."""
        return self.table_name