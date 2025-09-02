#!/usr/bin/env python3
"""
开发环境启动脚本
同时启动前端和后端服务，并处理跨域问题
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

class DevServer:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
    def start_backend(self):
        """启动后端服务"""
        print("🚀 启动后端服务...")
        backend_dir = Path("backend")
        if not backend_dir.exists():
            print("❌ 后端目录不存在")
            return False
            
        try:
            # 检查是否在虚拟环境中
            if os.path.exists("backend/venv"):
                python_cmd = "backend/venv/Scripts/python" if os.name == 'nt' else "backend/venv/bin/python"
            else:
                python_cmd = "python"
                
            self.backend_process = subprocess.Popen(
                [python_cmd, "main.py"],
                cwd="backend",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 等待后端启动
            time.sleep(3)
            if self.backend_process.poll() is None:
                print("✅ 后端服务启动成功 (http://127.0.0.1:8000)")
                return True
            else:
                print("❌ 后端服务启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动后端服务时出错: {e}")
            return False
    
    def start_frontend(self):
        """启动前端服务"""
        print("🚀 启动前端服务...")
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("❌ 前端目录不存在")
            return False
            
        try:
            # 检查是否有 package.json
            if not (frontend_dir / "package.json").exists():
                print("❌ 前端目录中没有 package.json")
                return False
                
            # 检查是否安装了依赖
            if not (frontend_dir / "node_modules").exists():
                print("📦 安装前端依赖...")
                subprocess.run(["npm", "install"], cwd="frontend", check=True)
                
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd="frontend",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 等待前端启动
            time.sleep(5)
            if self.frontend_process.poll() is None:
                print("✅ 前端服务启动成功 (http://localhost:3000)")
                return True
            else:
                print("❌ 前端服务启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动前端服务时出错: {e}")
            return False
    
    def monitor_processes(self):
        """监控进程输出"""
        def monitor_backend():
            if self.backend_process:
                for line in self.backend_process.stdout:
                    if self.running:
                        print(f"[后端] {line.rstrip()}")
                    else:
                        break
                        
        def monitor_frontend():
            if self.frontend_process:
                for line in self.frontend_process.stdout:
                    if self.running:
                        print(f"[前端] {line.rstrip()}")
                    else:
                        break
        
        # 启动监控线程
        if self.backend_process:
            threading.Thread(target=monitor_backend, daemon=True).start()
        if self.frontend_process:
            threading.Thread(target=monitor_frontend, daemon=True).start()
    
    def stop_services(self):
        """停止所有服务"""
        print("\n🛑 正在停止服务...")
        self.running = False
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            print("✅ 后端服务已停止")
            
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            print("✅ 前端服务已停止")
    
    def run(self):
        """运行开发服务器"""
        print("🎯 企业模型训练平台 - 开发环境启动器")
        print("=" * 50)
        
        # 启动后端
        if not self.start_backend():
            print("❌ 无法启动后端服务，退出")
            return 1
            
        # 启动前端
        if not self.start_frontend():
            print("❌ 无法启动前端服务，退出")
            self.stop_services()
            return 1
        
        # 启动监控
        self.monitor_processes()
        
        print("\n🎉 开发环境启动完成！")
        print("📱 前端地址: http://localhost:3000")
        print("🔧 后端地址: http://127.0.0.1:8000")
        print("📚 API文档: http://127.0.0.1:8000/docs")
        print("\n按 Ctrl+C 停止服务")
        
        try:
            # 保持运行
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 收到停止信号")
        finally:
            self.stop_services()
            
        return 0

def main():
    server = DevServer()
    sys.exit(server.run())

if __name__ == "__main__":
    main()

