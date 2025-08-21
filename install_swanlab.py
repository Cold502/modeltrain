#!/usr/bin/env python3
"""
SwanLab 安装脚本
用于快速安装和配置 SwanLab 训练可视化工具
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_command(cmd, check=True):
    """运行命令并处理错误"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {cmd}")
        print(f"错误信息: {e.stderr}")
        return None

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True

def install_swanlab():
    """安装SwanLab"""
    print("🔧 开始安装 SwanLab...")
    
    # 检查是否已安装
    result = run_command("swanlab --version", check=False)
    if result:
        print("✅ SwanLab 已安装")
        return True
    
    # 安装SwanLab
    print("📦 正在安装 SwanLab...")
    result = run_command("pip install swanlab")
    if not result:
        print("❌ SwanLab 安装失败")
        return False
    
    print("✅ SwanLab 安装成功")
    return True

def create_swanlab_config():
    """创建SwanLab配置文件"""
    config = {
        "host": "localhost",
        "port": 5092,
        "data_dir": "./swanlab_data",
        "project_name": "modeltrain"
    }
    
    config_file = "swanlab_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ SwanLab 配置文件已创建: {config_file}")
    return config

def create_data_directory():
    """创建数据目录"""
    data_dir = Path("./swanlab_data")
    data_dir.mkdir(exist_ok=True)
    print(f"✅ 数据目录已创建: {data_dir.absolute()}")
    return str(data_dir)

def test_swanlab_installation():
    """测试SwanLab安装"""
    print("🧪 测试 SwanLab 安装...")
    
    # 检查版本
    version = run_command("swanlab --version")
    if version:
        print(f"✅ SwanLab 版本: {version}")
    
    # 检查帮助信息
    help_info = run_command("swanlab --help")
    if help_info:
        print("✅ SwanLab 命令可用")
        return True
    
    return False

def create_startup_script():
    """创建启动脚本"""
    script_content = '''#!/bin/bash
# SwanLab 启动脚本

echo "🚀 启动 SwanLab 服务..."

# 检查配置文件
if [ ! -f "swanlab_config.json" ]; then
    echo "❌ 配置文件不存在，请先运行安装脚本"
    exit 1
fi

# 读取配置
HOST=$(python -c "import json; print(json.load(open('swanlab_config.json'))['host'])")
PORT=$(python -c "import json; print(json.load(open('swanlab_config.json'))['port'])")
DATA_DIR=$(python -c "import json; print(json.load(open('swanlab_config.json'))['data_dir'])")

echo "📍 服务地址: http://$HOST:$PORT"
echo "📁 数据目录: $DATA_DIR"

# 启动服务
swanlab ui --host $HOST --port $PORT --data-dir $DATA_DIR
'''
    
    script_file = "start_swanlab.sh"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod(script_file, 0o755)
    print(f"✅ 启动脚本已创建: {script_file}")

def main():
    """主函数"""
    print("=" * 50)
    print("🚀 SwanLab 安装脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装SwanLab
    if not install_swanlab():
        sys.exit(1)
    
    # 测试安装
    if not test_swanlab_installation():
        print("❌ SwanLab 安装测试失败")
        sys.exit(1)
    
    # 创建配置
    config = create_swanlab_config()
    
    # 创建数据目录
    data_dir = create_data_directory()
    
    # 创建启动脚本
    create_startup_script()
    
    print("\n" + "=" * 50)
    print("🎉 SwanLab 安装完成！")
    print("=" * 50)
    print(f"📍 服务地址: http://{config['host']}:{config['port']}")
    print(f"📁 数据目录: {data_dir}")
    print(f"⚙️  配置文件: swanlab_config.json")
    print(f"🚀 启动脚本: start_swanlab.sh")
    print("\n📖 使用方法:")
    print("1. 运行启动脚本: ./start_swanlab.sh")
    print("2. 在浏览器中访问: http://localhost:5092")
    print("3. 在训练可视化页面中管理SwanLab服务")
    print("\n💡 提示: 您也可以在训练可视化页面中直接启动SwanLab服务")

if __name__ == "__main__":
    main() 