import psycopg2
import os
import sys
import dotenv
from pathlib import Path

# Add parent directory to path to import from database module
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.connections.rds_postgres import PostgresConnection

def delete_database(db_name):
    """
    Deletes a PostgreSQL database using configuration from .env file
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
        
        # Check if our database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if exists:
            # Terminate all connections to the database before dropping
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = %s
                AND pid <> pg_backend_pid()
            """, (db_name,))
            
            # Drop the database
            cursor.execute(f"DROP DATABASE \"{db_name}\"")
            print(f"Database '{db_name}' has been deleted successfully.")
        else:
            print(f"Database '{db_name}' does not exist.")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error deleting database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    db_name="user"
    delete_database(db_name=db_name)