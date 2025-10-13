from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)
from app.schemas.user import UserRegister, UserLogin, PasswordReset, UserResponse, LoginResponse
from app.schemas.common import ErrorResponse
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
    """用户注册

    作用：
    - 创建新用户，返回用户基础信息（不含敏感字段）。

    触发链路：
    - 前端提交邮箱/昵称/密码 → 校验唯一性 → 写入数据库 → 返回 `UserResponse`。

    参数：
    - user_data：请求体（邮箱、昵称、密码）。
    - db：数据库会话（依赖注入）。

    返回：
    - 200 + `UserResponse`（创建成功）。

    注意：
    - 若邮箱/昵称已存在，抛 `HTTP_400`，由全局处理器封装为标准错误返回。
    """
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

@router.post("/login", response_model=LoginResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def login(user_data: UserLogin, response: Response, request: Request, db: Session = Depends(get_db)):
    """用户登录

    作用：
    - 验证账号密码，签发 Access Token，并通过 HttpOnly Cookie 设置 Refresh Token。

    触发链路：
    - 前端提交登录标识（邮箱或昵称）与密码 → 验证 → 生成双 token → 返回体含 access_token，Cookie 中写入 refresh_token。

    参数：
    - user_data：登录请求体（login, password）。
    - response：用于设置 Cookie。
    - request：仅用于最小调试/记录上下文。
    - db：数据库会话。

    返回：
    - 200 + `LoginResponse`（含 access_token），refresh_token 仅在 Cookie。

    注意：
    - 账号不存在/密码错误/账号禁用分别抛出 404/401/403，由全局异常处理统一响应格式。
    - Cookie `secure` 受环境变量 `COOKIE_SECURE` 控制。
    """
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
        import os
        cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=cookie_secure,  # 从环境变量读取
            samesite="lax",  # 使用lax，通过代理解决跨域
            max_age=7 * 24 * 60 * 60,  # 7天
            path="/",  # 确保cookie在所有路径下可用
            domain=None  # 不设置domain，让浏览器自动处理
        )
        
        logger.info(f"用户 {user.nickname} 登录成功")
        logger.debug(f"Cookie设置参数: httponly=True, secure={cookie_secure}, samesite=lax")
        
        # 调试信息（仅在开发环境输出）
        logger.debug(f"请求URL: {request.url}")
        logger.debug(f"请求域名: {request.base_url}")
        
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
        logger.error(f"登录过程中出现错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中出现内部错误"
        )

from fastapi import Cookie

@router.post("/refresh", responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def refresh_token(
    request: Request,
    refresh_token: str = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    """刷新访问令牌

    作用：
    - 使用 HttpOnly Cookie 中的 Refresh Token 换取新的 Access Token。

    触发链路：
    - 前端在 401 时调用 → 后端从 Cookie 读取 refresh_token → 校验合法与用户状态 → 返回新 access_token。

    参数：
    - request：请求上下文（记录最小信息）。
    - refresh_token：从 Cookie 读取的刷新令牌（别名 `refresh_token`）。
    - db：数据库会话。

    返回：
    - 200 + { access_token, token_type }。

    注意：
    - 缺少/无效/过期的 refresh_token 将返回 401 标准错误结构。
    """
    try:
        logger.info("收到refresh token请求")
        logger.debug(f"请求URL: {request.url}")
        logger.debug(f"请求域名: {request.base_url}")
        
        if not refresh_token:
            # 尝试从请求头中获取所有cookie
            cookie_header = request.headers.get("cookie", "")
            logger.debug(f"Cookie头存在: {bool(cookie_header)}")
            
            # 尝试手动解析cookie
            if "refresh_token=" in cookie_header:
                import re
                match = re.search(r'refresh_token=([^;]+)', cookie_header)
                if match:
                    refresh_token = match.group(1)
                    logger.debug("从Cookie头解析到refresh_token")
        
        if not refresh_token:
            logger.warning("缺少刷新令牌")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少刷新令牌"
            )
        
        # 验证refresh token
        payload = verify_refresh_token(refresh_token)
        if payload is None:
            logger.warning("刷新令牌无效或已过期")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌无效或已过期"
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            logger.error("刷新令牌格式错误")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌格式错误"
            )
        
        # 检查用户是否存在
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        if not user.is_active:
            logger.warning(f"用户账号已被禁用: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用"
            )
        
        # 生成新的access token
        new_access_token = create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"用户 {user.nickname} 的token刷新成功")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌过程中出现错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌过程中出现内部错误"
        )

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """重置密码

    作用：
    - 根据登录标识（邮箱/昵称）重置密码（示例实现）。

    参数：
    - reset_data：包含 login（邮箱/昵称）与 new_password。
    - db：数据库会话。

    返回：
    - 200 + { message }。

    注意：
    - 真实业务需接入验证码/双重校验/限流策略，防止撞库与滥用。
    """
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

@router.post("/logout", responses={200: {"description": "OK"}, 500: {"model": ErrorResponse}})
async def logout(response: Response):
    """用户登出

    作用：
    - 清除 HttpOnly Cookie 中的 refresh_token，令刷新能力失效。

    参数：
    - response：用于回写删除 Cookie 的指令（delete_cookie）。

    返回：
    - 200 + { message }。

    注意：
    - `secure/samesite/path/domain` 等参数需与 set_cookie 时保持一致，否则浏览器可能无法删除。
    """
    # 清除refresh token cookie
    import os
    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=cookie_secure,  # 从环境变量读取
        samesite="lax",  # 保持与设置时一致
        path="/",
        domain=None
    )
    logger.info("用户登出，refresh token cookie已清除")
    return {"message": "登出成功"}

@router.get("/me", response_model=UserResponse, responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息

    作用：
    - 基于 `Authorization: Bearer <access_token>` 已认证的用户，返回其基础信息。

    触发链路：
    - 依赖 `get_current_user` 完成 token 解码/校验与用户查询。

    参数：
    - current_user：认证通过的用户对象。

    返回：
    - 200 + `UserResponse`。

    注意：
    - access_token 无效/过期将触发 401，由全局异常处理统一响应。
    """
    return current_user 