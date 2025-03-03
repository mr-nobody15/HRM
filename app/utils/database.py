from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()


DATABASE_URL = "mysql+pymysql://admin:BiTs3678@airecruitpro.cfaq06062gu5.us-east-1.rds.amazonaws.com:3306/dev"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
Base = declarative_base()

# Create a new database
# db_name = "dev"
# try:
#     with engine.connect() as connection:
#         connection.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
#         print(f"Database '{db_name}' created successfully!")
# except Exception as e:
#     print(f"Error creating database: {e}")

# Dependency for database sessions


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()