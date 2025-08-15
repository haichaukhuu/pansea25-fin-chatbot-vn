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
                # Check if service account key file exists
                service_account_path = os.path.join(
                    os.path.dirname(__file__),
                    "firebase_credentials",
                    "service-account-key.json"
                )
                
                if os.path.exists(service_account_path):
                    # Initialize with service account credentials
                    cred = credentials.Certificate(service_account_path)
                    self.admin_app = firebase_admin.initialize_app(cred)
                else:
                    # Try to initialize with environment variable
                    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                    if google_creds:
                        cred = credentials.Certificate(google_creds)
                        self.admin_app = firebase_admin.initialize_app(cred)
                    else:
                        # Initialize with default credentials (works in Google Cloud)
                        self.admin_app = firebase_admin.initialize_app()
                
                self._initialized = True
                print("Firebase Admin SDK initialized successfully")
        
        except ValueError as e:
            if "already exists" in str(e):
                # App already initialized
                self.admin_app = firebase_admin.get_app()
                self._initialized = True
            else:
                raise e
        except Exception as e:
            print(f"Failed to initialize Firebase Admin SDK: {e}")
            raise e
    
    def initialize_client_sdk(self) -> None:
        """Initialize Firebase Client SDK for authentication operations"""
        try:
            # Load Firebase client configuration
            firebase_config = {
                "apiKey": os.getenv("FIREBASE_API_KEY"),
                "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                "projectId": os.getenv("FIREBASE_PROJECT_ID"),
                "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
                "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
                "appId": os.getenv("FIREBASE_APP_ID"),
                "databaseURL": f"https://{os.getenv('FIREBASE_PROJECT_ID', 'agrifinhub')}-default-rtdb.firebaseio.com/"
            }
            
            # Initialize Pyrebase client for auth operations
            self.client_app = pyrebase.initialize_app(firebase_config)
            print("Firebase Client SDK initialized successfully")
            
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
