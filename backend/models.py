from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Driver(Base):
    __tablename__ = 'drivers'
    id = Column(Integer, primary_key=True)
    whatsapp_number = Column(String, unique=True, nullable=False)
    calendar_token = Column(String)  # We'll store JSON string of tokens
    email = Column(String)

# SQLite database file will be created in the project root
engine = create_engine('sqlite:///taxitranslator.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)