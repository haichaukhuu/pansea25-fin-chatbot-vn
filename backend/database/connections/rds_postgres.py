from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import logging
from config import Config

logger = logging.getLogger(__name__)

class PostgresConnection:
    """PostgreSQL connection manager for AWS RDS"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.db_session = None
        self.Base = declarative_base()
    
    def initialize(self):
        """Initialize the database connection"""
        try:
            # Get connection string from config
            database_url = Config.RDS_DATABASE_URL
            
            if not database_url:
                logger.error("DATABASE_URL environment variable is not set")
                raise ValueError("DATABASE_URL environment variable is not set")
            
            # Create SQLAlchemy engine
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=5,
                max_overflow=10
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create a scoped session for thread safety
            self.db_session = scoped_session(self.SessionLocal)
            
            # Set query property on Base
            self.Base.query = self.db_session.query_property()
            
            logger.info("PostgreSQL connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection: {str(e)}")
            raise
    
    def create_tables(self):
        """Create all tables in the database"""
        try:
            # Import all models here to ensure they're registered
            from database.models.user import User
            
            self.Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    @contextmanager
    def get_db_session(self):
        """Get a database session with context management"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_db(self):
        """Get a database session (for use with FastAPI Depends)"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

# Create a singleton instance
postgres_connection = PostgresConnection()