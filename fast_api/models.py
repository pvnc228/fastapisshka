from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Session, relationship
from database import Base
from utils import hash_password

class Cart(Base):
    __tablename__ = "carts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)

    user = relationship("User", back_populates="cart")
    product = relationship("Product", back_populates="cart")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    cart = relationship("Cart", back_populates="user")
    # @staticmethod
    # def create_user(db: Session, email: str, password: str):
    #     hashed_password = hash_password(password)
    #     user = User(email=email, hashed_password=hashed_password)
    #     db.add(user)
    #     db.commit()
    #     db.refresh(user)
    #     return user

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text)
    price = Column(Integer)
    insurance_type = Column(String(50))  # Тип страхования (КАСКО, ОСАГО и т.д.)
    cart = relationship("Cart", back_populates="product")