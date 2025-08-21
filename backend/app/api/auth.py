from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.user import UserRegister, UserLogin, PasswordReset, UserResponse, LoginResponse
from app.utils.auth import (
    authenticate_user, 
    create_user, 
    get_user_by_email, 
    get_user_by_nickname,
    get_password_hash,
    create_access_token,
    get_current_user,
    create_refresh_token,
    verify_refresh_token
)
from app.models.user import User
from pydantic import BaseModel

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
async def login(user_data: UserLogin, response: Response, request: Request, db: Session = Depends(get_db)):
    """用户登录"""
    try:
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
        
        # 给用户制作两张通行证
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # 设置HttpOnly Cookie存储refresh token
        # 关键：确保cookie能正确设置，支持跨域
        # 使用代理后，可以使用更简单的Cookie设置
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # 开发环境设为False，生产环境应设为True
            samesite="lax",  # 使用lax，通过代理解决跨域
            max_age=7 * 24 * 60 * 60,  # 7天
            path="/",  # 确保cookie在所有路径下可用
            domain=None  # 不设置domain，让浏览器自动处理
        )
        
        print(f"✅ 用户 {user.nickname} 登录成功")
        print(f"🔑 Access token: {access_token[:20]}...")
        print(f"🔄 Refresh token: {refresh_token[:20]}...")
        print(f"🍪 Cookie设置参数:")
        print(f"   - key: refresh_token")
        print(f"   - value: {refresh_token[:20]}...")
        print(f"   - httponly: True")
        print(f"   - secure: False")
        print(f"   - samesite: lax")
        print(f"   - path: /")
        print(f"   - max_age: 7天")
        
        # 打印请求头信息用于调试
        print(f"📋 请求头: {dict(request.headers)}")
        print(f"🌐 请求URL: {request.url}")
        print(f"🏠 请求域名: {request.base_url}")
        
        # 验证cookie是否设置成功
        print(f"🍪 响应头中的Set-Cookie: {response.headers.get('set-cookie', '未找到')}")
        
        return LoginResponse(
            user=user, 
            message="登录成功", 
            access_token=access_token,
            refresh_token=None  # 不再返回refresh token到响应体
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"登录过程中出现错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中出现内部错误"
        )

from fastapi import Cookie

@router.post("/refresh")
async def refresh_token(
    request: Request,
    refresh_token: str = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        print(f"🔄 收到refresh token请求")
        print(f"📋 请求头: {dict(request.headers)}")
        print(f"🍪 Cookie中的refresh_token: {'存在' if refresh_token else '不存在'}")
        print(f"🌐 请求URL: {request.url}")
        print(f"🏠 请求域名: {request.base_url}")
        print(f"🔗 请求来源: {request.headers.get('origin', '未知')}")
        print(f"🌍 用户代理: {request.headers.get('user-agent', '未知')}")
        
        if refresh_token:
            print(f"🔍 Refresh token内容: {refresh_token[:20]}...")
        else:
            # 尝试从请求头中获取所有cookie
            cookie_header = request.headers.get("cookie", "")
            print(f"🍪 所有Cookie头: {cookie_header}")
            
            # 尝试手动解析cookie
            if "refresh_token=" in cookie_header:
                import re
                match = re.search(r'refresh_token=([^;]+)', cookie_header)
                if match:
                    refresh_token = match.group(1)
                    print(f"🔍 从Cookie头解析到refresh_token: {refresh_token[:20]}...")
                else:
                    print("❌ 无法从Cookie头解析refresh_token")
            else:
                print("❌ Cookie头中没有refresh_token")
                
            # 检查其他可能的cookie名称
            all_cookies = cookie_header.split(';')
            print(f"🍪 所有Cookie列表:")
            for cookie in all_cookies:
                cookie = cookie.strip()
                if cookie:
                    print(f"   - {cookie}")
        
        if not refresh_token:
            print("❌ 缺少刷新令牌")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少刷新令牌"
            )
        
        # 验证refresh token
        payload = verify_refresh_token(refresh_token)
        if payload is None:
            print("❌ 刷新令牌无效或已过期")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌无效或已过期"
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            print("❌ 刷新令牌格式错误")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌格式错误"
            )
        
        # 检查用户是否存在
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            print(f"❌ 用户不存在: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        if not user.is_active:
            print(f"❌ 用户账号已被禁用: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用"
            )
        
        # 生成新的access token
        new_access_token = create_access_token(data={"sub": str(user.id)})
        
        print(f"✅ 用户 {user.nickname} 的token刷新成功")
        print(f"🔑 新Access token: {new_access_token[:20]}...")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"刷新令牌过程中出现错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌过程中出现内部错误"
        )

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

@router.post("/logout")
async def logout(response: Response):
    """用户登出"""
    # 清除refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,  # 开发环境设为False，生产环境应设为True
        samesite="lax",  # 保持与设置时一致
        path="/",
        domain=None
    )
    print("✅ 用户登出，refresh token cookie已清除")
    return {"message": "登出成功"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user 