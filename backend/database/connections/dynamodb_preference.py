import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from typing import Optional, Dict, Any
from config import get_aws_preference_config

logger = logging.getLogger(__name__)

class PreferenceConnection:
    """Manages preference storage connections and operations."""
    
    def __init__(self):
        self._resource = None
        self._client = None
        self._config = get_aws_preference_config()
        
    def get_resource(self):
        """Get or create preference storage resource."""
        if self._resource is None:
            try:
                self._resource = boto3.resource(
                    'dynamodb',
                    region_name=self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key']
                )
                logger.info(f"Preference storage resource connected to region: {self._config['region']}")
            except Exception as e:
                logger.error(f"Failed to create preference storage resource: {e}")
                raise
        return self._resource
    
    def get_client(self):
        """Get or create preference storage client."""
        if self._client is None:
            try:
                self._client = boto3.client(
                    'dynamodb',
                    region_name=self._config['region'],
                    aws_access_key_id=self._config['access_key_id'],
                    aws_secret_access_key=self._config['secret_access_key']
                )
                logger.info(f"Preference storage client connected to region: {self._config['region']}")
            except Exception as e:
                logger.error(f"Failed to create preference storage client: {e}")
                raise
        return self._client
    
    def get_table(self, table_name: str):
        """Get a specific preference table."""
        try:
            resource = self.get_resource()
            table = resource.Table(table_name)
            
            # Verify table exists by calling describe_table
            table.load()
            logger.info(f"Successfully connected to preference table: {table_name}")
            return table
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Preference table {table_name} not found")
                raise Exception(f"Preference table '{table_name}' does not exist")
            else:
                logger.error(f"Failed to access preference table {table_name}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error accessing preference table {table_name}: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check preference storage connection health."""
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
                "message": "Preference storage connection successful"
            }
        except NoCredentialsError:
            return {
                "status": "unhealthy",
                "error": "AWS credentials not found",
                "message": "Check AWS_PREFERENCE_ACCESS_KEY_ID and AWS_PREFERENCE_SECRET_ACCESS_KEY"
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            return {
                "status": "unhealthy",
                "error": error_code,
                "message": f"Preference storage client error: {e.response['Error']['Message']}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(type(e).__name__),
                "message": str(e)
            }

# Global connection instance
preference_connection = PreferenceConnection()

def get_preference_table(table_name: str = None):
    """Get preference table instance."""
    if table_name is None:
        config = get_aws_preference_config()
        table_name = config['table_name']
    return preference_connection.get_table(table_name)

def get_preference_health():
    """Get preference storage connection health status."""
    return preference_connection.health_check()

def test_preference_connection():
    """Test preference storage connection and return status."""
    health = get_preference_health()
    if health["status"] == "healthy":
        print(f"Preference storage connection successful")
        print(f"Region: {health['region']}")
        print(f"Table: {health['table_name']}")
        print(f"Status: {health['table_status']}")
        return True
    else:
        print(f"Preference storage connection failed")
        print(f"Error: {health['error']}")
        print(f"Message: {health['message']}")
        return False

# Legacy function names for backward compatibility
dynamodb_connection = preference_connection
get_dynamodb_table = get_preference_table
get_dynamodb_health = get_preference_health
test_dynamodb_connection = test_preference_connection
