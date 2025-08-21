#!/usr/bin/env python3
"""
跨域配置测试脚本
用于验证前端和后端的跨域配置是否正常工作
"""

import requests
import json
import time

def test_backend_health():
    """测试后端健康检查"""
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        print(f"✅ 后端健康检查成功: {response.status_code}")
        print(f"   响应内容: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 后端健康检查失败: {e}")
        return False

def test_cors_preflight():
    """测试CORS预检请求"""
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
        response = requests.options('http://127.0.0.1:8000/api/auth/login', headers=headers, timeout=5)
        print(f"✅ CORS预检请求成功: {response.status_code}")
        print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
        print(f"   Access-Control-Allow-Credentials: {response.headers.get('Access-Control-Allow-Credentials')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS预检请求失败: {e}")
        return False

def test_frontend_proxy():
    """测试前端代理"""
    try:
        response = requests.get('http://localhost:3000/api/health', timeout=5)
        print(f"✅ 前端代理测试成功: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 前端代理测试失败: {e}")
        return False

def main():
    print("🔍 开始跨域配置测试...")
    print("=" * 50)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(2)
    
    # 测试后端
    print("\n1. 测试后端服务:")
    backend_ok = test_backend_health()
    
    # 测试CORS
    print("\n2. 测试CORS配置:")
    cors_ok = test_cors_preflight()
    
    # 测试前端代理
    print("\n3. 测试前端代理:")
    proxy_ok = test_frontend_proxy()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   后端服务: {'✅ 正常' if backend_ok else '❌ 异常'}")
    print(f"   CORS配置: {'✅ 正常' if cors_ok else '❌ 异常'}")
    print(f"   前端代理: {'✅ 正常' if proxy_ok else '❌ 异常'}")
    
    if all([backend_ok, cors_ok, proxy_ok]):
        print("\n🎉 所有测试通过！跨域配置正常。")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")
        if not backend_ok:
            print("   请确保后端服务在 http://127.0.0.1:8000 运行")
        if not cors_ok:
            print("   请检查后端的CORS配置")
        if not proxy_ok:
            print("   请确保前端服务在 http://localhost:3000 运行")

if __name__ == "__main__":
    main()

