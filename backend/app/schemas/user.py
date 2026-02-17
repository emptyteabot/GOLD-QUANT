"""用户schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)
