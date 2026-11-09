from pydantic import BaseModel, EmailStr, Field

# Gửi thông tin đăng ký 
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2, max_length=255)

# Trả về thông tin user sau khi đăng ký thành công
class UserRegisterResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True
        
# Gửi thông tin đăng nhập
class UserLoginRequest(BaseModel):
    email : EmailStr 
    password : str 
    
# Trả về thông tin user sau khi đăng nhập thành công
class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token : str 

    class Config:
        from_attributes = True

# Gửi thông tin account hiện tại 
class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True