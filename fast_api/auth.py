from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from schemas import UserCreate, UserResponse, Token
from utils import hash_password, verify_password, create_access_token
from datetime import timedelta

ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Токен будет действителен 30 минут

expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @router.post("/register", response_model=UserResponse)
# async def register(user: UserCreate, db: Session = Depends(get_db)):
#     # Проверка на существующего пользователя
#     db_user = db.query(User).filter(User.email == user.email).first()
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
    
#     # Хеширование пароля и сохранение в БД
#     hashed_password = hash_password(user.password)
#     new_user = User(email=user.email, hashed_password=hashed_password)
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    
    # Проверка на существующего пользователя
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Хеширование пароля и сохранение в БД
    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(user: UserCreate, db: Session = Depends(get_db)):
    # Проверка учетных данных
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Генерация токена
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}