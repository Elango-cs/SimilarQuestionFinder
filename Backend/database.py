import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Fetch database URL from environment variables, fallback to SQLite locally
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Render and Railway sometimes provide postgres:// which needs to be replaced with postgresql:// for SQLAlchemy
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    # Configure pool settings for PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )
else:
    DATABASE_URL = "sqlite:///./questions.db"
    # SQLite requires check_same_thread=False for multiple threads
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
