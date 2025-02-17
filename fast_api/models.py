from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from database import Base
from utils import hash_password

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    @staticmethod
    def create_user(db: Session, email: str, password: str):
        hashed_password = hash_password(password)
        user = User(email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user