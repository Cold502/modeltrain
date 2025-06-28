#!/usr/bin/env python3
"""
企业模型训练平台启动脚本
包含模型配置管理和多模型测试功能
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def run_command(command, cwd=None, shell=True):
    """运行命令"""
    try:
        if shell:
            subprocess.run(command, cwd=cwd, shell=True, check=True)
        else:
            subprocess.run(command, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False
    return True

def install_backend_deps():
    """安装后端依赖"""
    print("🔧 安装后端依赖...")
    os.chdir(BACKEND_DIR)
    
    # 检查是否存在虚拟环境
    venv_path = BACKEND_DIR / "venv"
    if not venv_path.exists():
        print("创建虚拟环境...")
        run_command("python -m venv venv")
    
    # 激活虚拟环境并安装依赖
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate && pip install -r requirements.txt"
    else:
        activate_cmd = "source venv/bin/activate && pip install -r requirements.txt"
    
    return run_command(activate_cmd)

def install_frontend_deps():
    """安装前端依赖"""
    print("🔧 安装前端依赖...")
    os.chdir(FRONTEND_DIR)
    return run_command("npm install")

def setup_database():
    """设置数据库"""
    print("🗄️ 设置数据库...")
    os.chdir(BACKEND_DIR)
    
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate && alembic upgrade head"
    else:
        activate_cmd = "source venv/bin/activate && alembic upgrade head"
    
    return run_command(activate_cmd)

def run_backend():
    """运行后端服务"""
    print("🚀 启动后端服务...")
    os.chdir(BACKEND_DIR)
    
    if sys.platform == "win32":
        cmd = "venv\\Scripts\\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    else:
        cmd = "source venv/bin/activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    
    subprocess.Popen(cmd, shell=True)

def run_frontend():
    """运行前端服务"""
    print("🌐 启动前端服务...")
    os.chdir(FRONTEND_DIR)
    subprocess.Popen("npm run dev", shell=True)

def check_dependencies():
    """检查依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查Python
    try:
        result = subprocess.run(["python", "--version"], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Python 未安装")
        return False
    
    # 检查Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✅ Node.js: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Node.js 未安装")
        return False
    
    # 检查npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print(f"✅ npm: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ npm 未安装")
        return False
    
    return True

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    企业模型训练平台                              ║
║              Enterprise Model Training Platform               ║
║                                                              ║
║  🔧 模型配置管理   📊 多模型对比测试   💬 智能对话               ║
║  🚀 模型训练      📈 可视化分析      🛠️ 提示词管理              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_urls():
    """打印访问地址"""
    print("\n" + "="*60)
    print("🌐 服务地址:")
    print("   前端地址: http://localhost:5173")
    print("   后端地址: http://localhost:8000")
    print("   API文档:  http://localhost:8000/docs")
    print("="*60)
    
    print("\n📋 功能说明:")
    print("   • 模型配置: 支持OpenAI、Ollama、DeepSeek等多种提供商")
    print("   • 模型测试: 最多选择3个模型进行对比测试")
    print("   • 流式输出: 支持实时流式响应和推理过程显示")
    print("   • 视觉模型: 支持图片上传和多模态对话")
    print("   • 用户管理: 简单的用户注册登录系统")
    print("="*60)
    
    print("\n🔐 默认管理员账号:")
    print("   用户名: admin")
    print("   密码:   admin")
    print("="*60)

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 系统依赖检查失败，请安装所需依赖")
        sys.exit(1)
    
    # 安装后端依赖
    if not install_backend_deps():
        print("❌ 后端依赖安装失败")
        sys.exit(1)
    
    # 安装前端依赖
    if not install_frontend_deps():
        print("❌ 前端依赖安装失败")
        sys.exit(1)
    
    # 设置数据库
    if not setup_database():
        print("⚠️ 数据库设置失败，但继续启动...")
    
    # 启动服务
    print("\n🚀 启动服务...")
    
    # 在单独的线程中启动后端
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # 等待后端启动
    print("⏳ 等待后端启动...")
    time.sleep(5)
    
    # 在单独的线程中启动前端
    frontend_thread = threading.Thread(target=run_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    # 等待前端启动
    print("⏳ 等待前端启动...")
    time.sleep(3)
    
    print_urls()
    
    print("\n✅ 服务启动完成!")
    print("按 Ctrl+C 停止服务")
    
    try:
        # 保持主进程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        print("服务已停止")

if __name__ == "__main__":
    main() 