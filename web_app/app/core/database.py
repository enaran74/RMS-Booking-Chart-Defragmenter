"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import DATABASE_URL, settings

# Create database engine with configuration to avoid transaction conflicts
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,    # Recycle connections every hour
    pool_size=5,          # Increase pool size to handle concurrent requests
    max_overflow=5,       # Allow more overflow connections
    pool_timeout=30,      # Reasonable timeout for connections
    pool_pre_ping=False,  # Disable ping to avoid transaction conflicts
    echo=False,           # Disable query logging to reduce overhead
    isolation_level="AUTOCOMMIT"  # Set isolation level to prevent transaction conflicts
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db() -> Session:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database with tables
    """
    Base.metadata.create_all(bind=engine)
