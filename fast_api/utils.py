from passlib.context  import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# Настройки для JWT
SECRET_KEY = "665aabf3428c87c0b11ae782dd740c8a20db6f3c2b3b9708bcb83b96270b5cf8b04b34088f7b8efdfdc9e20a34964145698702b6e852ac4cb119ab4873eebc4776dba4490443ad98f8cf27e54c373cbc482cc9c7be4d3efea2581a656d10842b6b18fb6e9fb317edc33575c310597313275558e849fd3544f40f6cd8414ac2b63ad8c43cfc8a89f246702ff39b6eaf8307f7eb9893cecaf1f901383de94f5c50aecc16e2236802950028772e3e97fad2466f1a0dee233b379b9474bed5847b746e7a6c41f0a06c700df9b79e46e2b3f496f99123c39f0342f3718fc4d874969b76d527e5ed2a944ca17dbf427beca04da61528716d50479fbc27dbc1a70018d5"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    print("token is created! ", jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

