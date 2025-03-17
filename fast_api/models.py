from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Date
from sqlalchemy.orm import Session, relationship
from database import Base
from utils import hash_password

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
    full_name = Column(String, nullable=True)  # Новое поле: ФИО
    phone_number = Column(String, nullable=True)  # Новое поле: номер телефона
    date_of_birth = Column(Date, nullable=True)  # Новое поле: дата рождения
    cart = relationship("Cart", back_populates="user")
    

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text)
    price = Column(Integer)
    insurance_type = Column(String(50))  # Тип страхования (КАСКО, ОСАГО и т.д.)
    cart = relationship("Cart", back_populates="product")
    # Новые поля
    max_car_age = Column(Integer)  # Максимальный возраст автомобиля
    insurance_amount = Column(Integer)  # Страховая сумма
    insurance_duration = Column(String(50))  # Срок страхования
    policy_cost = Column(Integer)  # Стоимость полиса
    risks = Column(Text)  # Страховые риски
    payment_conditions = Column(String(100))  # Условия оплаты
    client_service_24_7 = Column(Boolean, default=False)  # Клиентский сервис 24/7
    emergency_commissioner = Column(Boolean, default=False)  # Аварийный комиссар
    tow_truck = Column(Boolean, default=False)  # Эвакуатор
    compensation_form = Column(String(100))  # Форма возмещения
    payout_without_certificates = Column(Boolean, default=False)  # Выплата без справок