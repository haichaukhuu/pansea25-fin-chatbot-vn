from sqlalchemy.orm import Session
from database.models.user import User
from core.models.user import UserCreate, UserUpdate
import bcrypt
from typing import Optional, List
import uuid
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    """Data access layer for User operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user in the database."""
        try:
            # Hash the password
            hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
            
            # Create new user
            db_user = User(
                email=user_data.email,
                password_hash=hashed_password.decode('utf-8'),
                display_name=user_data.display_name
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            logger.info(f"Created new user with email: {user_data.email}")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        return self.db.query(User).all()
    
    def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """Update a user."""
        try:
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                logger.warning(f"Update attempted on non-existent user ID: {user_id}")
                return None
                
            # Update user data
            update_data = user_data.dict(exclude_unset=True)
            
            if 'password' in update_data and update_data['password']:
                # Hash the password if it's being updated
                hashed_password = bcrypt.hashpw(update_data['password'].encode('utf-8'), bcrypt.gensalt())
                setattr(db_user, 'password_hash', hashed_password.decode('utf-8'))
                del update_data['password']
            
            # Update remaining fields
            for key, value in update_data.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)
            
            self.db.commit()
            self.db.refresh(db_user)
            logger.info(f"Updated user with ID: {user_id}")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user: {str(e)}")
            raise
    
    def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete a user."""
        try:
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                logger.warning(f"Delete attempted on non-existent user ID: {user_id}")
                return False
                
            self.db.delete(db_user)
            self.db.commit()
            logger.info(f"Deleted user with ID: {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user: {str(e)}")
            raise
    
    def verify_password(self, user: User, password: str) -> bool:
        """Verify a user's password."""
        return bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))