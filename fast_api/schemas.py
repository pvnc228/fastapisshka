from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    email: EmailStr

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