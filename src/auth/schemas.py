from pydantic import BaseModel,Field,field_validator 
import re
from datetime import datetime 
import uuid 
from typing import List 


class EmailMixin(BaseModel):
    email: str = Field(..., max_length=40)

    @field_validator("email")
    def validate_email(cls, value: str) -> str:
        # RFC 5322 simplified regex for email validation
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.match(email_regex, value):
            raise ValueError("Invalid email format")
        return value
    
class PasswordMixin(BaseModel):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def validate_password(cls, value):
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_regex, value):
            raise ValueError(
                "Password must have ≥8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special symbol"
            )
        return value
    
class ConfirmPasswordMixin(BaseModel):
    confirm_password: str = Field(..., min_length=8)

    @field_validator("confirm_password")
    def passwords_match(cls, value, info):
        password = info.data.get("password")
        if password and value != password:
            raise ValueError("Passwords do not match")
        return value

class UserCreateModel(EmailMixin,PasswordMixin,ConfirmPasswordMixin):
    username: str = Field(..., max_length=50)
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)

class UserModel(EmailMixin):
    uid:uuid.UUID 
    username: str = Field(..., max_length=50)
    first_name: str=Field(...,min_length=2,max_length=100)
    last_name: str=Field(...,min_length=2,max_length=100)
    is_verified:bool 
    created_at:datetime
    updated_at:datetime 
    
class UserLoginModel(EmailMixin,PasswordMixin):
    pass 

class PasswordUpdateModel(PasswordMixin,ConfirmPasswordMixin):
    pass 

