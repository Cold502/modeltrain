from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
import os

from app.database import SessionLocal, engine, create_tables, get_db
from app.api import auth, chat, model, training, admin, model_config, playground
from app.models import user as user_models
from app.utils.auth import create_admin_user
from app.api.model_config import init_default_model_configs

app = FastAPI(
    title="企业模型训练平台",
    description="基于FastAPI的模型训练和测试平台",
    version="1.0.0"
)

# 跨域设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
create_tables()

# 初始化管理员账号和默认模型配置
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        # 创建管理员账号
        create_admin_user(db)
        # 初始化默认模型配置
        await init_default_model_configs(db)
    finally:
        db.close()

# 路由注册
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(model.router, prefix="/api/model", tags=["模型"])
app.include_router(training.router, prefix="/api/training", tags=["训练"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(model_config.router, prefix="/api", tags=["模型配置"])
app.include_router(playground.router, prefix="/api", tags=["模型测试"])

# 静态文件服务
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {"message": "企业模型训练平台 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    ) 