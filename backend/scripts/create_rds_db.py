import psycopg2
import os
import sys
import dotenv
from pathlib import Path

# Add parent directory to path to import from database module
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.connections.rds_postgres import PostgresConnection

def create_database(db_name):
    """
    Creates a PostgreSQL database using configuration from .env file
    """
    # Load environment variables
    dotenv.load_dotenv()
    
    # Get database connection parameters from environment
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    
    # Connect to default postgres database instead of the one we want to delete
    try:
        # Connect to postgres database (default database)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"  # Connect to default database
        )
        conn.autocommit = True  # Need autocommit for database operations
        cursor = conn.cursor()
        
        
        cursor.execute(f"CREATE DATABASE \"{db_name}\"")
        print(f"Database '{db_name}' has been created successfully.")

        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    db_name="user"
    create_database(db_name=db_name)