from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

class ContactModel(BaseModel):

    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr = Field(max_length=250)
    phone_number: str = Field(max_length=20)
    birthday: date
    information: Optional[str] = Field(default=None, max_length=500)

class ContactResponse(ContactModel):

    id: int

    model_config = ConfigDict(from_attributes=True)

class ContactUpdate(BaseModel):

    first_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=250)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    birthday: Optional[date] = None
    information: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(from_attributes=True)

class UserModel(BaseModel):

    username: EmailStr
    password: str = Field(min_length=2, max_length=255)

class UserResponse(BaseModel):

    id: int
    username: str = Field(validation_alias='email')
    avatar: str
    confirmed: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SignupResponse(BaseModel):

    user: UserResponse
    detail: str

class TokenResponse(BaseModel):

    access_token: str 
    refresh_token: str
    token_type: str = 'bearer'

class RequestEmail(BaseModel):

    email: EmailStr