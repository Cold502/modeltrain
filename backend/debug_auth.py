import requests
import json
import jwt
import sqlite3
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

def debug_auth():
    """调试认证问题"""
    print("=== 调试认证问题 ===")
    
    # 1. 登录获取token
    login_data = {
        "login": "admin",
        "password": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ 登录成功，获取到token: {token[:50]}...")
            
            # 2. 手动验证token
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                print(f"✅ Token验证成功: {payload}")
                user_id = payload.get('sub')
                print(f"用户ID: {user_id}")
            except Exception as e:
                print(f"❌ Token验证失败: {e}")
                return
            
            # 3. 检查数据库中的用户
            conn = sqlite3.connect('../modeltrain.db')
            cursor = conn.cursor()
            
            # 检查users表结构
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            print(f"\n数据库表结构:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 查询用户
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                print(f"✅ 数据库中找到用户: {user}")
            else:
                print(f"❌ 数据库中未找到用户ID: {user_id}")
                return
            
            # 4. 测试API调用
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"\n4. 测试API调用:")
            print(f"状态码: {me_response.status_code}")
            print(f"响应: {me_response.text}")
            
            if me_response.status_code == 200:
                print("✅ API调用成功")
            else:
                print("❌ API调用失败")
                
        else:
            print(f"❌ 登录失败: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    debug_auth() 