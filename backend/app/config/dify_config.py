"""
Dify配置文件
存储Dify API Key和服务地址
"""

import os
from pathlib import Path

# Dify服务配置
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost:5001")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "app-your-dify-api-key-here")

# Dify前端地址
DIFY_WEB_URL = os.getenv("DIFY_WEB_URL", "http://localhost:3000")

# 请求超时设置
DIFY_TIMEOUT = 60

# 是否启用Dify
DIFY_ENABLED = os.getenv("DIFY_ENABLED", "true").lower() == "true"
