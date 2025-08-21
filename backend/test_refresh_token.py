#!/usr/bin/env python3
"""
测试Refresh Token机制的脚本
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:8000/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
REFRESH_URL = f"{BASE_URL}/auth/refresh"
TEST_URL = f"{BASE_URL}/auth/me"

def test_refresh_token():
    """测试refresh token机制"""
    print("🧪 开始测试Refresh Token机制")
    print("=" * 50)
    
    # 创建session来保持cookie
    session = requests.Session()
    
    # 1. 登录
    print("1️⃣ 执行登录...")
    login_data = {
        "login": "admin",
        "password": "admin"
    }
    
    try:
        login_response = session.post(LOGIN_URL, json=login_data)
        print(f"   登录状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print(f"   登录成功: {login_result.get('message')}")
            print(f"   Access Token: {login_result.get('access_token', '')[:20]}...")
            
            # 检查cookie
            cookies = session.cookies.get_dict()
            print(f"   Cookies: {cookies}")
            
            # 检查refresh_token cookie
            if 'refresh_token' in cookies:
                print(f"   ✅ Refresh Token Cookie存在: {cookies['refresh_token'][:20]}...")
            else:
                print("   ❌ Refresh Token Cookie不存在")
                return False
                
        else:
            print(f"   ❌ 登录失败: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 登录异常: {e}")
        return False
    
    print()
    
    # 2. 测试正常请求
    print("2️⃣ 测试正常请求...")
    try:
        me_response = session.get(TEST_URL)
        print(f"   请求状态码: {me_response.status_code}")
        
        if me_response.status_code == 200:
            print("   ✅ 正常请求成功")
        else:
            print(f"   ❌ 正常请求失败: {me_response.text}")
            
    except Exception as e:
        print(f"   ❌ 正常请求异常: {e}")
    
    print()
    
    # 3. 测试refresh token
    print("3️⃣ 测试Refresh Token...")
    try:
        refresh_response = session.post(REFRESH_URL)
        print(f"   Refresh状态码: {refresh_response.status_code}")
        
        if refresh_response.status_code == 200:
            refresh_result = refresh_response.json()
            print(f"   ✅ Refresh成功")
            print(f"   新Access Token: {refresh_result.get('access_token', '')[:20]}...")
            
            # 再次测试请求
            print("   测试刷新后的请求...")
            me_response2 = session.get(TEST_URL)
            print(f"   请求状态码: {me_response2.status_code}")
            
            if me_response2.status_code == 200:
                print("   ✅ 刷新后请求成功")
                return True
            else:
                print(f"   ❌ 刷新后请求失败: {me_response2.text}")
                return False
                
        else:
            print(f"   ❌ Refresh失败: {refresh_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Refresh异常: {e}")
        return False

def test_cookie_headers():
    """测试Cookie头信息"""
    print("\n🔍 测试Cookie头信息")
    print("=" * 30)
    
    session = requests.Session()
    
    # 登录
    login_data = {"login": "admin", "password": "admin"}
    login_response = session.post(LOGIN_URL, json=login_data)
    
    if login_response.status_code == 200:
        print("✅ 登录成功")
        
        # 检查响应头中的Set-Cookie
        set_cookie = login_response.headers.get('Set-Cookie', '')
        print(f"Set-Cookie头: {set_cookie}")
        
        # 检查refresh_token是否在Set-Cookie中
        if 'refresh_token=' in set_cookie:
            print("✅ Refresh Token在Set-Cookie中")
        else:
            print("❌ Refresh Token不在Set-Cookie中")
        
        # 测试refresh请求的Cookie头
        refresh_response = session.post(REFRESH_URL)
        print(f"Refresh请求状态: {refresh_response.status_code}")
        
        # 打印session中的cookies
        print(f"Session Cookies: {dict(session.cookies)}")
        
    else:
        print("❌ 登录失败")

if __name__ == "__main__":
    print("🚀 启动Refresh Token测试")
    print("请确保后端服务正在运行 (http://localhost:8000)")
    print()
    
    # 测试Cookie头信息
    test_cookie_headers()
    
    print()
    
    # 测试完整流程
    success = test_refresh_token()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 Refresh Token机制测试成功！")
    else:
        print("❌ Refresh Token机制测试失败！")
    print("=" * 50)
