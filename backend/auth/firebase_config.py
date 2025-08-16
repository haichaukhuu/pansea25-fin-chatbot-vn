import os
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional
import pyrebase
import json
from dotenv import load_dotenv

load_dotenv()

class FirebaseConfig:
    """Firebase configuration and initialization"""
    
    def __init__(self):
        self.admin_app: Optional[firebase_admin.App] = None
        self.client_app = None
        self._initialized = False
    
    def initialize_admin_sdk(self) -> None:
        """Initialize Firebase Admin SDK"""
        try:
            if not self._initialized:
                # Check if service account key file exists in the same directory
                service_account_path = os.path.join(
                    os.path.dirname(__file__),
                    "service-account-key.json"
                )
                
                if os.path.exists(service_account_path):
                    # Initialize with service account credentials
                    cred = credentials.Certificate(service_account_path)
                    self.admin_app = firebase_admin.initialize_app(cred)
                    print(f"Firebase Admin SDK initialized with service account: {service_account_path}")
                else:
                    # Try to initialize with environment variable
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
                                    service_account_data = json.load(f)
                                    project_id = service_account_data.get("project_id")
                                
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
    
    def initialize_client_sdk(self) -> None:
        """Initialize Firebase Client SDK for authentication operations"""
        try:
            # Get project ID from service account if not in environment
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            if not project_id:
                try:
                    service_account_path = os.path.join(
                        os.path.dirname(__file__),
                        "service-account-key.json"
                    )
                    with open(service_account_path, 'r') as f:
                        service_account_data = json.load(f)
                        project_id = service_account_data.get("project_id", "agrifinhub")
                except (FileNotFoundError, json.JSONDecodeError, KeyError):
                    project_id = "agrifinhub"  # fallback
            
            # Load Firebase client configuration with fallbacks
            firebase_config = {
                "apiKey": os.getenv("FIREBASE_API_KEY", "default-api-key"),
                "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", f"{project_id}.firebaseapp.com"),
                "projectId": project_id,
                "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", f"{project_id}.appspot.com"),
                "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "123456789"),
                "appId": os.getenv("FIREBASE_APP_ID", "default-app-id"),
                "databaseURL": f"https://{project_id}-default-rtdb.firebaseio.com/"
            }
            
            # Check if required fields are present
            required_fields = ["apiKey", "authDomain", "projectId"]
            missing_fields = [field for field in required_fields if not firebase_config[field] or firebase_config[field].startswith("default-")]
            
            if missing_fields:
                print(f"Warning: Missing Firebase client configuration fields: {missing_fields}")
                print("Some authentication features may not work properly")
            
            # Initialize Pyrebase client for auth operations
            self.client_app = pyrebase.initialize_app(firebase_config)
            print(f"Firebase Client SDK initialized successfully with project: {project_id}")
            
        except Exception as e:
            print(f"Failed to initialize Firebase Client SDK: {e}")
            raise e
    
    def get_admin_auth(self):
        """Get Firebase Admin Auth instance"""
        if not self._initialized:
            self.initialize_admin_sdk()
        return auth
    
    def get_client_auth(self):
        """Get Firebase Client Auth instance"""
        if not self.client_app:
            self.initialize_client_sdk()
        return self.client_app.auth()

# Global Firebase instance
firebase_config = FirebaseConfig()
