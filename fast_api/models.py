from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Boolean, Date
from sqlalchemy.orm import Session, relationship
from database import Base
from utils import hash_password
from datetime import datetime

class Cart(Base):
    __tablename__ = "carts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    products_name = Column(String)  # Новое пол
    quantity = Column(Integer, default=1)

    user = relationship("User", back_populates="cart")
    product = relationship("Product", back_populates="cart")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)  
    phone_number = Column(String, nullable=True) 
    date_of_birth = Column(Date, nullable=True)  
    cart = relationship("Cart", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text)
    price = Column(Integer)
    insurance_type = Column(String(50))  
    
    image_url = Column(String(255))
    max_car_age = Column(Integer) 
    insurance_amount = Column(Integer)  
    insurance_duration = Column(String(50))  
    policy_cost = Column(Integer)  
    risks = Column(Text)  
    payment_conditions = Column(String(100))  
    client_service_24_7 = Column(Boolean, default=False)  
    emergency_commissioner = Column(Boolean, default=False)  
    tow_truck = Column(Boolean, default=False)  
    compensation_form = Column(String(100))  
    payout_without_certificates = Column(Boolean, default=False)
    reviews = relationship("Review", back_populates="product") 
    cart = relationship("Cart", back_populates="product") 

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    author = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    
    # Связь с пользователем
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="reviews")
    
    # Связь с товаром (если отзыв о товаре)
    product_id = Column(Integer, ForeignKey("products.id"))
    product = relationship("Product", back_populates="reviews")