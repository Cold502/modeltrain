from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.model import router as model_router
from app.api.training import router as training_router
from app.api.admin import router as admin_router
from app.api.model_config import router as model_config_router
from app.api.playground import router as playground_router

# 路由注册
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(chat_router, prefix="/api/chat", tags=["对话"])
app.include_router(model_router, prefix="/api/models", tags=["模型"])
app.include_router(training_router, prefix="/api/training", tags=["训练"])
app.include_router(admin_router, prefix="/api/admin", tags=["管理"])
app.include_router(model_config_router, prefix="/api", tags=["模型配置"])
app.include_router(playground_router, prefix="/api", tags=["模型测试"]) 