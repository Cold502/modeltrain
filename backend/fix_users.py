from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

def fix_users():
    """修复数据库中的用户"""
    db = SessionLocal()
    try:
        # 删除所有现有用户
        db.query(User).delete()
        db.commit()
        print("已清除所有用户")
        
        # 创建管理员用户
        admin_user = User(
            email="admin@modeltrain.com",
            nickname="admin",
            password_hash=get_password_hash("admin"),
            role="admin",
            is_admin=True,
            is_active=True
        )
        db.add(admin_user)
        
        # 创建测试用户
        test_user = User(
            email="test@example.com",
            nickname="testuser",
            password_hash=get_password_hash("testpassword123"),
            is_active=True
        )
        db.add(test_user)
        
        db.commit()
        print("用户创建成功:")
        print("管理员: admin / admin")
        print("测试用户: testuser / testpassword123")
        
        # 验证用户
        users = db.query(User).all()
        print(f"\n数据库中共有 {len(users)} 个用户:")
        for user in users:
            print(f"ID: {user.id}, 邮箱: {user.email}, 昵称: {user.nickname}, 管理员: {user.is_admin}")
            
    except Exception as e:
        print(f"修复用户失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_users() 