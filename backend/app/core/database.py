from sqlalchemy import create_engine, event, DDL
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
    from ..models.db import Base, MappingSession
    
    # Add event listener to create schema before creating tables
    event.listen(
        MappingSession.__table__,
        'before_create',
        DDL('CREATE SCHEMA IF NOT EXISTS pseudonymization'),
        once=True
    )
    
    # Create uuid extension
    with engine.begin() as conn:
        conn.execute(DDL('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
    
    # Now create all tables
    Base.metadata.create_all(bind=engine)