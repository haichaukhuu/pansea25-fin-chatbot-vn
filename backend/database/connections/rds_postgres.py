from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from config import Config

# Create the SQLAlchemy engine
DATABASE_URL = Config.DATABASE_URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a scoped session for thread safety
db_session = scoped_session(SessionLocal)

Base = declarative_base()
Base.query = db_session.query_property()

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database by creating all tables."""
    # Import all models that need to be created
    from database.models.user import User
    Base.metadata.create_all(bind=engine)