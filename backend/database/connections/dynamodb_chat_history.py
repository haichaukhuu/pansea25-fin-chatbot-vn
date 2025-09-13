import boto3
import os
import logging
from botocore.exceptions import ClientError

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
            # Using default AWS credentials from environment variables
            self.client = boto3.client(
                'dynamodb',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'ap-southeast-2')
            )
            self.table_name = os.getenv('CHAT_HISTORY_TABLE_NAME')
            logger.info(f"DynamoDB connection initialized for table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB connection: {str(e)}")
            raise
    
    def get_client(self):
        """Returns the DynamoDB client."""
        return self.client
    
    def get_table_name(self):
        """Returns the DynamoDB table name."""
        return self.table_name