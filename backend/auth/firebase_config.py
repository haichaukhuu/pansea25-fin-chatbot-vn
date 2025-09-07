import os
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional
import json
from dotenv import load_dotenv
import json
from dotenv import load_dotenv

# Load environment variables from multiple possible locations
load_dotenv()  # Load from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))  # Load from auth directory
load_dotenv(os.path.join(os.path.dirname(__file__), 'firebase_credentials', '.env'))  # Load from firebase_credentials
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))  # Load from backend directory

class FirebaseConfig:
    """Firebase configuration and initialization"""
    
    def __init__(self):
        self.admin_app: Optional[firebase_admin.App] = None
        self._initialized = False
    
    def _get_service_account_from_env(self) -> Optional[dict]:
        """Extract service account credentials from environment variable"""
        try:
            service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
            if service_account_json:
                # Parse the JSON string from environment variable
                service_account_data = json.loads(service_account_json)
                
                # Handle newline characters in private_key
                if 'private_key' in service_account_data:
                    service_account_data['private_key'] = service_account_data['private_key'].replace('\\n', '\n')
                
                return service_account_data
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing FIREBASE_SERVICE_ACCOUNT from environment: {e}")
        return None
    
    def initialize_admin_sdk(self) -> None:
        """Initialize Firebase Admin SDK"""
        try:
            if not self._initialized:
                # First, try to get service account from environment variable
                service_account_data = self._get_service_account_from_env()
                if service_account_data:
                    cred = credentials.Certificate(service_account_data)
                    self.admin_app = firebase_admin.initialize_app(cred)
                    print("Firebase Admin SDK initialized with service account from environment variable")
                else:
                    # Fallback to service account file in the same directory
                    service_account_path = os.path.join(
                        os.path.dirname(__file__),
                        "firebase_credentials",
                        "service-account-key.json"
                    )
                    
                    if os.path.exists(service_account_path):
                        # Initialize with service account credentials
                        cred = credentials.Certificate(service_account_path)
                        self.admin_app = firebase_admin.initialize_app(cred)
                        print(f"Firebase Admin SDK initialized with service account file: {service_account_path}")
                    else:
                        # Try to initialize with GOOGLE_APPLICATION_CREDENTIALS environment variable
                        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                        if google_creds:
                            cred = credentials.Certificate(google_creds)
                            self.admin_app = firebase_admin.initialize_app(cred)
                            print(f"Firebase Admin SDK initialized with GOOGLE_APPLICATION_CREDENTIALS: {google_creds}")
                        else:
                            # Try to get project ID from environment or service account
                            project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
                            
                            if project_id:
                                # Initialize with project ID
                                self.admin_app = firebase_admin.initialize_app(options={"projectId": project_id})
                                print(f"Firebase Admin SDK initialized with project ID: {project_id}")
                            else:
                                # Try to read project ID from service account file
                                try:
                                    with open(service_account_path, 'r') as f:
                                        service_account_file_data = json.load(f)
                                        project_id = service_account_file_data.get("project_id")
                                    
                                    if project_id:
                                        self.admin_app = firebase_admin.initialize_app(options={"projectId": project_id})
                                        print(f"Firebase Admin SDK initialized with project ID from service account: {project_id}")
                                    else:
                                        raise ValueError("No project ID found in service account or environment variables")
                                except (FileNotFoundError, json.JSONDecodeError, KeyError):
                                    raise ValueError("No project ID found in service account or environment variables")
                
                self._initialized = True
                print("Firebase Admin SDK initialized successfully")
        
        except ValueError as e:
            if "already exists" in str(e):
                # App already initialized
                self.admin_app = firebase_admin.get_app()
                self._initialized = True
                print("Firebase Admin SDK already initialized")
            else:
                print(f"Firebase Admin SDK initialization failed: {e}")
                raise e
        except Exception as e:
            print(f"Failed to initialize Firebase Admin SDK: {e}")
            raise e
    
    def get_admin_auth(self):
        """Get Firebase Admin Auth instance"""
        if not self._initialized:
            self.initialize_admin_sdk()
        return auth

# Global Firebase instance
firebase_config = FirebaseConfig()
