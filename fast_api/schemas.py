from pydantic import BaseModel, EmailStr
from datetime import date

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None  # Новое поле
    phone_number: str | None = None  # Новое поле
    date_of_birth: date | None = None  # Новое поле

class UserResponse(BaseModel):
    email: EmailStr
    full_name: str | None  # Новое поле
    phone_number: str | None  # Новое поле
    date_of_birth: date | None  # Новое поле

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
class EditEmailRequest(BaseModel):
    new_email: str
    password: str

class EditPasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str