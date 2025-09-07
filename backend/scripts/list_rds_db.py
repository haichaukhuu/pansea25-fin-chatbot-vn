"""
Script to list all databases in the RDS PostgreSQL instance.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def list_databases():
    """
    List all databases in the RDS PostgreSQL instance.
    """
    try:
        # Connect to the default 'postgres' database to list all databases
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database="postgres"  # Connect to default postgres database
        )
        conn.autocommit = True
        
        # Create cursor
        cursor = conn.cursor()
        
        # Execute query to list databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        
        # Fetch all database names
        databases = cursor.fetchall()
        
        print("RDS PostgreSQL Databases:")
        print("-------------------------")
        for db in databases:
            print(f"- {db[0]}")
            
        cursor.close()
        conn.close()
        
        return databases
        
    except Exception as e:
        print(f"Error listing databases: {e}")
        return None

if __name__ == "__main__":
    list_databases()