from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

# Gửi thông tin đăng ký 
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    username: Optional[str] = None

# Trả về thông tin user sau khi đăng ký thành công
class UserRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    email: str
    username: str
    role: Optional[str] = "USER"
    status: Optional[str] = "ACTIVE"
    created_at: Optional[datetime] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
        
# Gửi thông tin đăng nhập (chấp nhận email hoặc username)
class UserLoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str
    
# Trả về thông tin user sau khi đăng nhập thành công
class UserLoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    role: Optional[str] = None

# Gửi thông tin account hiện tại 
class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    role: str
    status: str

class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
