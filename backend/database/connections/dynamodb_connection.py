"""
DynamoDB connection management for user preferences storage.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from typing import Optional, Dict, Any
from config import get_aws_dynamodb_config

logger = logging.getLogger(__name__)

class DynamoDBConnection:
    """Manages DynamoDB connections and operations."""
    
    def __init__(self):
        self._resource = None
        self._client = None
        self._config = get_aws_dynamodb_config()
        
    def get_resource(self):
        """Get or create DynamoDB resource."""
        if self._resource is None:
            try:
                self._resource = boto3.resource(
                    'dynamodb',
                    region_name=self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key']
                )
                logger.info(f"DynamoDB resource connected to region: {self._config['region']}")
            except Exception as e:
                logger.error(f"Failed to create DynamoDB resource: {e}")
                raise
        return self._resource
    
    def get_client(self):
        """Get or create DynamoDB client."""
        if self._client is None:
            try:
                self._client = boto3.client(
                    'dynamodb',
                    region_name=self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key']
                )
                logger.info(f"DynamoDB client connected to region: {self._config['region']}")
            except Exception as e:
                logger.error(f"Failed to create DynamoDB client: {e}")
                raise
        return self._client
    
    def get_table(self, table_name: str):
        """Get a specific DynamoDB table."""
        try:
            resource = self.get_resource()
            table = resource.Table(table_name)
            
            # Verify table exists by calling describe_table
            table.load()
            logger.info(f"Successfully connected to table: {table_name}")
            return table
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Table {table_name} not found")
                raise Exception(f"DynamoDB table '{table_name}' does not exist")
            else:
                logger.error(f"Failed to access table {table_name}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error accessing table {table_name}: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check DynamoDB connection health."""
        try:
            client = self.get_client()
            
            # Test basic connectivity
            response = client.list_tables(Limit=1)
            
            # Test table access
            table_name = self._config['table_name']
            table = self.get_table(table_name)
            
            return {
                "status": "healthy",
                "region": self._config['region'],
                "table_name": table_name,
                "table_status": table.table_status,
                "message": "DynamoDB connection successful"
            }
        except NoCredentialsError:
            return {
                "status": "unhealthy",
                "error": "AWS credentials not found",
                "message": "Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            return {
                "status": "unhealthy",
                "error": error_code,
                "message": f"DynamoDB client error: {e.response['Error']['Message']}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(type(e).__name__),
                "message": str(e)
            }

# Global connection instance
dynamodb_connection = DynamoDBConnection()

def get_dynamodb_table(table_name: str = None):
    """Get DynamoDB table instance."""
    if table_name is None:
        config = get_aws_dynamodb_config()
        table_name = config['table_name']
    return dynamodb_connection.get_table(table_name)

def get_dynamodb_health():
    """Get DynamoDB connection health status."""
    return dynamodb_connection.health_check()

def test_dynamodb_connection():
    """Test DynamoDB connection and return status."""
    health = get_dynamodb_health()
    if health["status"] == "healthy":
        print(f"✅ DynamoDB connection successful")
        print(f"   Region: {health['region']}")
        print(f"   Table: {health['table_name']}")
        print(f"   Status: {health['table_status']}")
        return True
    else:
        print(f"❌ DynamoDB connection failed")
        print(f"   Error: {health['error']}")
        print(f"   Message: {health['message']}")
        return False
