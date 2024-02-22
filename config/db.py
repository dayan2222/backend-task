from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime

# Database setup
DATABASE_URL = "sqlite:///./test.db"
Base = declarative_base()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"

    email = Column(String, primary_key=True, index=True)
    hashed_password = Column(String)


Base.metadata.create_all(bind=engine)