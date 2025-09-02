import sqlite3
import hashlib
import bcrypt
from datetime import datetime

def create_admin_user():
    """直接创建管理员用户"""
    conn = sqlite3.connect('../modeltrain.db')
    cursor = conn.cursor()
    
    try:
        # 检查users表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("users表不存在，创建表...")
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR UNIQUE,
                    nickname VARCHAR,
                    password_hash VARCHAR,
                    role VARCHAR DEFAULT 'user',
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # 删除现有的admin用户
        cursor.execute("DELETE FROM users WHERE nickname = 'admin'")
        
        # 创建新的admin用户
        password = "admin"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO users (email, nickname, password_hash, role, is_admin, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("admin@modeltrain.com", "admin", password_hash, "admin", True, True))
        
        conn.commit()
        print("✅ 管理员用户创建成功")
        print("用户名: admin")
        print("密码: admin")
        
        # 验证用户
        cursor.execute("SELECT id, email, nickname, is_admin FROM users")
        users = cursor.fetchall()
        print(f"\n数据库中共有 {len(users)} 个用户:")
        for user in users:
            print(f"ID: {user[0]}, 邮箱: {user[1]}, 昵称: {user[2]}, 管理员: {user[3]}")
            
    except Exception as e:
        print(f"创建用户失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin_user() 