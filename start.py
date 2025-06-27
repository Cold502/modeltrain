import subprocess
import sys
import os
import time

# 安装Python依赖
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# 启动后端（新窗口）
if os.name == 'nt':  # Windows
    subprocess.Popen('start "后端" cmd /k "cd backend && python main.py"', shell=True)
else:  # Linux/Mac
    subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 'cd backend && python main.py; exec bash'])

time.sleep(2)

# 启动前端
os.chdir('frontend')
subprocess.run('npm install', shell=True)
subprocess.run('npm run dev', shell=True) 