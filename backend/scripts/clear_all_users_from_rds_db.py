"""
Script to delete all users from the database without deleting the database itself.
This is useful for testing or resetting user data.

Usage:
    python delete_all_users.py

Options:
    --confirm: Skip the confirmation prompt (use with caution)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connections.rds_postgres import get_db_session
from database.models.user import User
from sqlalchemy.exc import SQLAlchemyError
import argparse

def delete_all_users(skip_confirmation=False):
    """Delete all users from the database."""
    
    if not skip_confirmation:
        confirmation = input("Are you sure you want to delete ALL users? This action cannot be undone. (y/n): ")
        if confirmation.lower() != 'y':
            print("Operation cancelled.")
            return
    
    try:
        session = next(get_db_session())
        deleted_count = session.query(User).delete()
        session.commit()
        print(f"Successfully deleted {deleted_count} users from the database.")
        
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error deleting users: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete all users from the database")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    delete_all_users(args.confirm)