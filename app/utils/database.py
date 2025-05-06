from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import logging
from urllib.parse import quote_plus

load_dotenv()

# Database credentials
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
print(DB_PASSWORD , "DB_PASSWORD")



def format_db_url(user, password, host, port, dbname, dialect="mysql", driver="pymysql"):
    encoded_user = quote_plus(user)
    encoded_password = quote_plus(password)
    return f"{dialect}+{driver}://{encoded_user}:{encoded_password}@{host}:{port}/{dbname}"

def get_connection():
    try:
        # Create database URL with proper formatting
        DATABASE_URL = format_db_url(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
        print(DATABASE_URL)
        engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=0,
            pool_timeout=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        print(f"Connection to {DB_HOST} for user {DB_USER} created successfully.")
        return engine
    except Exception as ex:
        print("Connection could not be made due to the following error: \n", ex)
        raise

# Create engine
engine = get_connection()
# Create session factory
SessionLocal = sessionmaker(bind=engine)
# Create base for models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()