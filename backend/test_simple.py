import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_simple():
    """简单测试"""
    print("=== 简单测试 ===")
    
    # 1. 测试健康检查
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"健康检查: {response.status_code}")
    except Exception as e:
        print(f"健康检查失败: {e}")
    
    # 2. 测试登录
    login_data = {
        "login": "admin",
        "password": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"获取到通行证: {token[:30]}...")
            
            # 3. 测试获取用户信息
            headers = {"Authorization": f"Bearer {token}"}  # 在请求头中带上通行证
            me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"获取用户信息状态码: {me_response.status_code}")
            print(f"响应: {me_response.text}")
            
        else:
            print(f"登录失败: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_simple() 