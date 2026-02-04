from fastapi import FastAPI, Depends, HTTPException, status  # FastAPI 核心框架与常用类型
from fastapi.middleware.cors import CORSMiddleware  # CORS 中间件，用于跨域设置
from fastapi.staticfiles import StaticFiles  # 静态资源服务
from sqlalchemy.orm import Session  # SQLAlchemy 会话类型
import uvicorn  # 开发调试服务器
import os  # 读取环境变量
import logging  # 统一日志接口
from dotenv import load_dotenv  # 读取 .env 文件中的环境变量
from contextlib import asynccontextmanager  # 用于新版 lifespan
import subprocess  # 启动子进程（如 LLaMA-Factory）

from app.database import SessionLocal, engine, get_db  # 数据库会话工厂与依赖
from app.api import auth, chat, model, training, admin, model_config, playground, dify  # 各业务路由模块
# 导入所有模型以确保 Base.metadata.create_all 能创建所有表
from app.models import user, chat as chat_models, model as model_models, model_config as model_config_models, training as training_models
from app.utils.auth import create_admin_user  # 管理员初始化工具
from app.api.model_config import init_default_model_configs  # 默认模型配置初始化
from app.schemas.common import ErrorResponse, ErrorDetail  # 统一错误响应模型

# 读取 backend/.env（确保无论从哪里启动都能加载到）
# 作用（为什么存在）：
# - 将 JWT_SECRET_KEY / COOKIE_SECURE / ENVIRONMENT 等敏感或可变配置从代码中剥离，统一通过环境变量控制。
# 触发（何时生效）：
# - 应用启动导入本模块时立即执行，加载 .env 内容到进程环境。
# 注意：
# - 生产环境使用系统环境变量或安全的密钥管理服务，不应把 .env 提交到仓库。
# dotenv_path：后端目录下的 .env 文件绝对路径
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# 配置日志
# 作用：
# - 提供统一的日志级别与格式，便于排错与日志聚合。
# 触发：
# - 模块导入时配置全局 logging。
# 参数说明：
# - level：根据 ENVIRONMENT 控制日志级别（生产 INFO，开发 DEBUG）。
# - format：统一日志输出格式（时间-模块-级别-消息）。
logging.basicConfig(
    level=logging.INFO if os.getenv("ENVIRONMENT", "development") == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# logger：本模块专用日志记录器
logger = logging.getLogger(__name__)

# lifespan：应用生命周期管理（新版写法）
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    作用：
    - 在应用启动时创建数据库表、初始化默认数据
    - 在应用关闭时执行清理操作
    
    触发：
    - FastAPI 启动/关闭时自动调用
    """
    # 启动时执行
    logger.info("应用启动中...")

    # 启动 LLaMA-Factory Web UI（端口 7860）
    llamafactory_proc = None
    try:
        logger.info("尝试启动 LLaMA-Factory Web UI（llamafactory-cli webui --port 7860）...")
        llamafactory_proc = subprocess.Popen(
            ["llamafactory-cli", "webui", "--port", "7860"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info("LLaMA-Factory Web UI 子进程已启动，PID=%s", llamafactory_proc.pid)
    except FileNotFoundError:
        logger.error("无法找到 'llamafactory-cli' 命令，请确认 LLaMA-Factory 已正确安装到当前环境中。")
    except Exception as e:
        logger.error("启动 LLaMA-Factory Web UI 失败: %s", e)

    # 创建所有表（如果不存在）
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表结构已创建或已存在")

    # 初始化默认数据
    db = SessionLocal()
    try:
        create_admin_user(db)  # 确保默认管理员账号存在
        await init_default_model_configs(db)  # 初始化默认模型配置
    finally:
        db.close()

    logger.info("应用启动完成")
    
    yield  # 应用运行期间
    
    # 关闭时执行（可选）
    logger.info("应用关闭中...")

    # 关闭 LLaMA-Factory 子进程（如果有）
    if llamafactory_proc is not None:
        try:
            logger.info("尝试关闭 LLaMA-Factory Web UI 子进程（PID=%s）...", llamafactory_proc.pid)
            llamafactory_proc.terminate()
            llamafactory_proc.wait(timeout=10)
            logger.info("LLaMA-Factory Web UI 子进程已正常退出。")
        except Exception as e:
            logger.error("关闭 LLaMA-Factory Web UI 子进程失败: %s", e)

# app：FastAPI 应用实例
# 作用：
# - 承载路由、依赖、中间件与异常处理，生成 OpenAPI 文档。
# 参数：
# - title/description/version：用于 OpenAPI 文档展示。
# - lifespan：生命周期管理器
app = FastAPI(
    title="企业模型训练平台",
    description="基于FastAPI的模型训练和测试平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 跨域中间件设置
# 作用：
# - 允许前端（开发环境）携带 Cookie 访问后端接口，解决跨域限制。
# 触发：
# - 每个请求都会经过中间件，校验请求的 Origin/Headers/Methods。
# 参数说明：
# - allow_origins：允许的来源（Origin），需与前端 dev server 保持一致。
# - allow_credentials：允许携带 Cookie（配合 HttpOnly Refresh Token 使用）。
# - allow_methods/allow_headers：允许的方法与头部（生产环境建议最小化）。
# 注意：
# - 生产环境应改为实际域名，避免使用通配；减少暴露的 headers。
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["Content-Type", "Authorization"] if os.getenv("ENVIRONMENT", "development") == "production" else ["*"]
)

# 全局异常处理，将各类异常统一映射为 ErrorResponse，以便前端稳定处理
from fastapi import Request  # Request：当前请求上下文
from fastapi.responses import JSONResponse  # JSONResponse：返回 JSON 结构
from fastapi.exceptions import RequestValidationError  # RequestValidationError：请求体验证失败
from starlette.exceptions import HTTPException as StarletteHTTPException  # Starlette 层的 HTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 异常处理器

    作用（为什么存在）：
    - 通过装饰器 `@app.exception_handler(StarletteHTTPException)` 注册为“处理 HTTP 异常”的全局处理器，统一输出标准错误响应结构。

    触发链路（何时被调用）：
    - 路由/依赖中显式 `raise HTTPException(...)` → Starlette/ FastAPI 的 ExceptionMiddleware 捕获 → 根据异常类型匹配到本处理器 → 返回 JSON 错误响应。

    参数：
    - request：请求上下文（仅用于采集必要调试信息，如 URL）。
    - exc：HTTP 异常对象（包含 `status_code` 与 `detail`）。

    返回：
    - 标准化错误结构 `ErrorResponse`，code 形如 `HTTP_<status>`，生产环境不包含 debug。

    注意：
    - 仅负责处理 HTTP 层面异常；更具体/其他类型异常由其它处理器负责。
    """
    # 统一封装为标准错误结构，debug 仅在开发环境提供最小上下文
    logger.warning(f"HTTPException: {exc.status_code} {exc.detail}")
    payload = ErrorResponse(
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            debug=None if os.getenv("ENVIRONMENT", "development") == "production" else {
                "path": str(request.url),
            },
        )
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求参数校验异常处理器

    作用（为什么存在）：
    - 通过装饰器 `@app.exception_handler(RequestValidationError)` 注册为“处理请求体验证失败”的全局处理器，统一返回 422 与标准错误结构，避免默认 HTML 错误页。

    触发链路（何时被调用）：
    - FastAPI 在路由执行前对路径/查询/Body 做 Pydantic 校验 → 校验失败时自动抛出 `RequestValidationError`（无需手动 raise）→ 中间件捕获 → 调用本处理器。

    参数：
    - request：请求上下文。
    - exc：校验异常对象，包含字段级错误列表 `exc.errors()`。

    返回：
    - 422 状态码与 `ErrorResponse`。开发环境返回详细 `debug`（字段错误列表），生产环境隐藏。

    注意：
    - 本处理器只负责“校验失败”类异常；其它异常由对应处理器兜底。
    """
    logger.warning(f"ValidationError: {exc}")
    payload = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Validation failed",
            debug=None if os.getenv("ENVIRONMENT", "development") == "production" else exc.errors(),
        )
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """兜底异常处理器（未捕获的异常）

    作用（为什么存在）：
    - 通过装饰器 `@app.exception_handler(Exception)` 注册为“处理所有未被更具体处理器接管的异常”的兜底处理器，确保始终返回 JSON 错误结构并避免泄露。

    触发链路（何时被调用）：
    - 路由/依赖执行过程中发生任意未捕获异常 → ExceptionMiddleware 捕获 → 没有更具体的处理器匹配 → 调用本处理器。

    参数：
    - request：请求上下文。
    - exc：任意 Python 异常实例。

    返回：
    - 500 状态码与 `ErrorResponse`。生产环境隐藏 debug（错误详情/堆栈），开发环境提供最小信息辅助排查。

    注意：
    - 请勿在此返回敏感信息；敏感内容只允许在开发环境用于调试。
    """
    logger.error(f"UnhandledException: {exc}")
    payload = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="Internal server error",
            debug=None if os.getenv("ENVIRONMENT", "development") == "production" else str(exc),
        )
    )
    return JSONResponse(status_code=500, content=payload.model_dump())

# 路由注册
# 作用：
# - 汇总各业务模块的路由到统一应用实例。
# 参数说明：
# - prefix：统一的接口前缀，便于网关/代理配置与权限控制。
# - tags：OpenAPI 文档中的分组标签，便于分类与浏览。
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(model.router, prefix="/api/model", tags=["模型"])
app.include_router(training.router, prefix="/api/training", tags=["训练"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(model_config.router, prefix="/api", tags=["模型配置"])
app.include_router(playground.router, prefix="/api/playground", tags=["Playground"])
app.include_router(dify.router, prefix="/api/dify", tags=["Dify"])

# 静态文件服务
# 作用：
# - 提供固定文件（如导出结果、用户上传）的 HTTP 访问。
# 触发：
# - 应用启动时检查目录存在与否；请求 `/uploads/*` 时由 StaticFiles 处理。
# 注意：
# - 上传安全与访问控制应在业务层或网关层加强（此处仅暴露目录）。
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    """健康首页：用于检查服务是否启动成功

    作用：
    - 提供一个最简单的可用性探测端点。

    返回：
    - 固定 JSON。可被监控与反向代理健康检查使用。
    """
    return {"message": "企业模型训练平台 API"}

@app.get("/health")
async def health_check():
    """健康检查端点：供监控/探活使用

    作用：
    - 供负载均衡/监控系统进行心跳探测。

    返回：
    - 固定 JSON（也可扩展为返回依赖服务状态）。
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    # 直接运行本文件时启动开发服务器（仅开发调试用）
    # host：监听地址；port：端口；reload：代码变更自动重载；log_level：uvicorn 日志级别
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )