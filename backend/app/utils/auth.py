from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, password_hash: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, password_hash)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def authenticate_user(db: Session, login: str, password: str) -> User:
    """验证用户登录"""
    # 可以使用邮箱或昵称登录
    user = db.query(User).filter(
        (User.email == login) | (User.nickname == login)
    ).first()
    
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
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
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("默认管理员账号已创建：admin / admin")

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