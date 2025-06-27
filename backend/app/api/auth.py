from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.user import UserRegister, UserLogin, PasswordReset, UserResponse, LoginResponse
from app.utils.auth import (
    authenticate_user, 
    create_user, 
    get_user_by_email, 
    get_user_by_nickname,
    get_password_hash
)
from app.models.user import User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已存在
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 检查昵称是否已存在
    if get_user_by_nickname(db, user_data.nickname):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="昵称已被使用"
        )
    
    # 创建用户
    user = create_user(db, user_data.email, user_data.nickname, user_data.password)
    return user

@router.post("/login", response_model=LoginResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, user_data.login, user_data.password)
    
    if not user:
        # 检查用户是否存在
        existing_user = db.query(User).filter(
            (User.email == user_data.login) | (User.nickname == user_data.login)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="密码错误"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="邮箱或昵称不存在"
            )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    return LoginResponse(user=user, message="登录成功")

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """重置密码"""
    user = db.query(User).filter(
        (User.email == reset_data.login) | (User.nickname == reset_data.login)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮箱或昵称不存在"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(reset_data.new_password)
    db.commit()
    
    return {"message": "密码重置成功"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """获取当前用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user 