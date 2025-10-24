import bcrypt
from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta, timezone  # 添加 timezone
from typing import Optional
from app.database import get_db
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


# 加载环境变量（显式定位到 backend/.env）
_backend_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(dotenv_path=_backend_env_path)

# JWT令牌配置 - 从环境变量读取
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

security = HTTPBearer()


def verify_password(plain_password: str, password_hash: str) -> bool:
    """验证密码 - 使用 bcrypt 5.x 新API"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"密码验证失败: {e}")
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希 - 使用 bcrypt 5.x 新API"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建刷新令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """检查通行证是否有效 - 解密并验证用户通行证"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # 用秘密配方解密通行证
        logger.debug("通行证验证成功")
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("通行证已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"通行证验证失败: {e}")
        return None
    except Exception as e:
        logger.error(f"通行证检查出现异常: {e}")
        return None

def verify_refresh_token(token: str) -> Optional[dict]:
    """检查刷新通行证是否有效"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 检查是否是refresh token
        if payload.get("type") != "refresh":
            logger.warning("Token类型错误，不是refresh token")
            return None
        logger.debug("刷新通行证验证成功")
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("刷新通行证已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"刷新通行证验证失败: {e}")
        return None
    except Exception as e:
        logger.error(f"刷新通行证检查出现异常: {e}")
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """根据通行证找到当前用户 - 检查通行证并返回对应的用户信息"""
    try:
        token = credentials.credentials  # 从请求中拿到用户的通行证
        logger.debug("验证token")
        
        payload = verify_token(token)  # 检查通行证是否有效
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="通行证无效或已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id: str = payload.get("sub")  # 从通行证中提取用户ID
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="通行证格式错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 根据用户ID从数据库查找用户信息
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            
            if user is None:
                logger.warning(f"数据库中未找到用户ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                logger.warning(f"用户账号已被禁用: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="账号已被禁用",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.debug(f"成功获取用户对象: {user.email}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"数据库查询错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="数据库查询错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户认证错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user_optional(db: Session = Depends(get_db)):
    """获取当前用户（可选）- 用于不需要强制认证的API，有通行证就用，没有就算了"""
    from fastapi import Header
    from typing import Optional
    
    async def _get_current_user_optional(authorization: Optional[str] = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            return None  # 没有通行证就算了
        
        token = authorization.replace("Bearer ", "")  # 去掉"Bearer "前缀，拿到纯通行证
        payload = verify_token(token)  # 检查通行证
        if payload is None:
            return None  # 通行证无效就算了
        
        user_id: str = payload.get("sub")  # 从通行证中提取用户ID
        if user_id is None:
            return None  # 通行证格式不对就算了
        
        user = db.query(User).filter(User.id == int(user_id)).first()  # 根据ID找用户
        return user
    
    return _get_current_user_optional

def authenticate_user(db: Session, login: str, password: str) -> User:
    """验证用户登录"""
    # 可以使用邮箱或昵称登录
    user = db.query(User).filter(
        (User.email == login) | (User.nickname == login)
    ).first()
    
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_admin_user(db: Session):
    """创建默认管理员账号"""
    admin_user = db.query(User).filter(User.nickname == "admin").first()
    if not admin_user:
        admin_user = User(
            email="admin@modeltrain.com",
            nickname="admin",
            password_hash=get_password_hash("admin"),
            role="admin",
            is_admin=True,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        logger.info("默认管理员账号已创建：admin / admin")
    else:
        # 如果admin用户已存在但is_admin为False，更新为True
        if not admin_user.is_admin:
            admin_user.is_admin = True
            admin_user.role = "admin"
            db.commit()
            logger.info("admin用户权限已更新为管理员")

def get_user_by_email(db: Session, email: str) -> User:
    """通过邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_nickname(db: Session, nickname: str) -> User:
    """通过昵称获取用户"""
    return db.query(User).filter(User.nickname == nickname).first()

def create_user(db: Session, email: str, nickname: str, password: str) -> User:
    """创建新用户"""
    password_hash = get_password_hash(password)
    db_user = User(
        email=email,
        nickname=nickname,
        password_hash=password_hash
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user 