from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    from ..models.db import Base
    
    # Create pseudonymization schema first
    with engine.begin() as conn:
        # Create uuid extension if not exists
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        # Create schema if not exists
        conn.execute(text('CREATE SCHEMA IF NOT EXISTS pseudonymization'))
    
    # Now create all tables
    Base.metadata.create_all(bind=engine)