from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.utils.auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有用户列表（管理员）"""
    admin_user = current_user
    if not admin_user or not admin_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    users = db.query(User).all()
    return users

@router.delete("/users/{target_user_id}")
async def delete_user(
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户（管理员）"""
    admin_user = current_user
    if not admin_user or not admin_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.nickname == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除admin用户"
        )
    
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账号"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"用户 {user.nickname} 已删除"}

@router.put("/users/{target_user_id}/role")
async def update_user_role(
    target_user_id: int,
    request_body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改用户角色（管理员）"""
    # 从请求体中获取is_admin
    is_admin = request_body.get("is_admin")
    if is_admin is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少is_admin参数"
        )
    
    admin_user = current_user
    if not admin_user or not admin_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    user.is_admin = is_admin
    # 保持与字符串角色字段同步，便于数据库直观显示
    user.role = "admin" if is_admin else "user"
    db.commit()
    db.refresh(user)
    
    role_name = "管理员" if is_admin else "普通用户"
    return {"message": f"用户 {user.nickname} 的角色已修改为 {role_name}"}

@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统统计信息（管理员）"""
    admin_user = current_user
    if not admin_user or not admin_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_users
        }
    } 