from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# 用户注册请求
class UserRegister(BaseModel):
    email: EmailStr
    nickname: str
    password: str

# 用户登录请求
class UserLogin(BaseModel):
    login: str  # 可以是邮箱或昵称
    password: str

# 重置密码请求
class PasswordReset(BaseModel):
    login: str  # 可以是邮箱或昵称
    new_password: str

# 用户响应
class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    is_admin: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# 用户更新
class UserUpdate(BaseModel):
    email: Optional[str] = None
    nickname: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

# 登录响应
class LoginResponse(BaseModel):
    user: UserResponse
    message: str 