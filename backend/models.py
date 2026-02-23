from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Base class for all our database tables
Base = declarative_base()

# Table for drivers
class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    whatsapp_number = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False)  # used for Google Calendar
    calendar_token = Column(String)         # will store JSON of OAuth tokens

# SQLite database file (will be created automatically in project root)
engine = create_engine("sqlite:///taxitranslator.db", echo=False)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables (only runs once, safe to call multiple times)
Base.metadata.create_all(bind=engine)