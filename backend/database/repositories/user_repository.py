from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any, List

from database.models.user import User

class UserRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_user(self, email: str, hashed_password: str, display_name: str = None) -> User:
        """Create a new user in the database"""
        user = User(
            email=email,
            hashed_password=hashed_password,
            display_name=display_name if display_name else email.split('@')[0]
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("User with this email already exists")

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
                
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user from database"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
            
        self.db.delete(user)
        self.db.commit()
        return True
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get a list of users"""
        return self.db.query(User).offset(skip).limit(limit).all()