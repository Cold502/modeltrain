from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

def check_users():
    """检查数据库中的用户"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"数据库中共有 {len(users)} 个用户:")
        for user in users:
            print(f"ID: {user.id}, 邮箱: {user.email}, 昵称: {user.nickname}, 管理员: {user.is_admin}, 激活: {user.is_active}")
    finally:
        db.close()

def create_test_user():
    """创建测试用户"""
    db = SessionLocal()
    try:
        # 检查是否已存在测试用户
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print("测试用户已存在，删除旧用户")
            db.delete(existing_user)
            db.commit()
        
        # 创建新的测试用户
        test_user = User(
            email="test@example.com",
            nickname="testuser",
            password_hash=get_password_hash("testpassword123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        print("测试用户创建成功")
    except Exception as e:
        print(f"创建测试用户失败: {e}")
        db.rollback()
    finally:
        db.close()

def fix_admin_user():
    """修复管理员用户"""
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.nickname == "admin").first()
        if admin_user:
            print("管理员用户已存在，更新密码")
            admin_user.password_hash = get_password_hash("admin")
            admin_user.is_admin = True
            admin_user.is_active = True
            db.commit()
            print("管理员用户密码已更新")
        else:
            print("创建管理员用户")
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
            print("管理员用户创建成功")
    except Exception as e:
        print(f"修复管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 检查现有用户 ===")
    check_users()
    
    print("\n=== 修复管理员用户 ===")
    fix_admin_user()
    
    print("\n=== 创建测试用户 ===")
    create_test_user()
    
    print("\n=== 检查修复后的用户 ===")
    check_users() 