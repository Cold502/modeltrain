from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import os
import logging

from app.database import SessionLocal
from app.models.model import Model, ModelTest
from app.schemas.user import UserResponse
from app.schemas.common import ErrorResponse
from app.utils.auth import get_current_user
from app.models.user import User

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    """数据库会话依赖注入
    
    作用：
    - 为每个请求提供数据库会话，确保事务正确管理。
    
    触发链路：
    - FastAPI 依赖注入系统自动调用。
    
    参数：
    - 无直接参数，通过 Depends() 注入。
    
    返回：
    - 生成器，yield 数据库会话对象。
    
    注意：
    - 使用 try/finally 确保会话正确关闭，避免连接泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 模型管理
@router.get("/list", responses={500: {"model": ErrorResponse}})
async def get_models(db: Session = Depends(get_db)):
    """获取所有可用模型列表
    
    作用：
    - 返回系统中所有状态为可用的模型信息。
    
    触发链路：
    - 前端模型选择页面调用。
    
    参数：
    - db：数据库会话依赖注入。
    
    返回：
    - 200 + 模型列表（包含 id、name、display_name、status、model_type、parameters、description）。
    
    注意：
    - 仅返回 is_available=True 的模型；参数以字符串形式存储。
    """
    models = db.query(Model).filter(Model.is_available == True).all()
    return [
        {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "status": model.status,
            "model_type": model.model_type,
            "parameters": model.parameters,
            "description": model.description
        }
        for model in models
    ]

@router.post("/load/{model_id}", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def load_model(model_id: int, db: Session = Depends(get_db)):
    """加载模型到 VLLM
    
    作用：
    - 将指定模型加载到 VLLM 推理引擎中，使其可用于推理。
    
    触发链路：
    - 用户在前端点击"加载模型"按钮。
    
    参数：
    - model_id：要加载的模型 ID。
    - db：数据库会话依赖注入。
    
    返回：
    - 200 + { message, status }。
    
    注意：
    - 当前为模拟实现，实际需要调用 VLLM API；状态会从 loading 变为 active 或 error。
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # TODO: 实际的VLLM模型加载逻辑
    # 这里先模拟加载过程
    try:
        model.status = "loading"
        db.commit()
        
        # 模拟加载时间
        import asyncio
        await asyncio.sleep(2)
        
        model.status = "active"
        db.commit()
        
        return {"message": f"模型 {model.display_name} 加载成功", "status": "active"}
    except Exception as e:
        model.status = "error"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模型加载失败: {str(e)}"
        )

@router.post("/unload/{model_id}", responses={404: {"model": ErrorResponse}})
async def unload_model(model_id: int, db: Session = Depends(get_db)):
    """卸载模型
    
    作用：
    - 从 VLLM 推理引擎中卸载指定模型，释放内存资源。
    
    触发链路：
    - 用户在前端点击"卸载模型"按钮。
    
    参数：
    - model_id：要卸载的模型 ID。
    - db：数据库会话依赖注入。
    
    返回：
    - 200 + { message, status }。
    
    注意：
    - 当前为模拟实现，实际需要调用 VLLM API；状态变为 inactive。
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # TODO: 实际的VLLM模型卸载逻辑
    model.status = "inactive"
    db.commit()
    
    return {"message": f"模型 {model.display_name} 已卸载", "status": "inactive"}

# 模型测试
@router.post("/test", responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def test_models(
    test_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试多个模型对比
    
    作用：
    - 使用相同输入测试多个模型，返回对比结果并保存测试记录。
    
    触发链路：
    - 用户在模型测试页面提交测试请求。
    
    参数：
    - test_data：包含 models（模型名列表）、input（输入文本）、streaming（是否流式）的字典。
    - db/current_user：依赖注入。
    
    返回：
    - 200 + { test_id, results }。
    
    注意：
    - 最多同时测试 3 个模型；当前为模拟实现，实际需要调用各模型推理 API。
    """
    models_to_test = test_data.get("models", [])
    input_text = test_data.get("input", "")
    is_streaming = test_data.get("streaming", False)
    
    if len(models_to_test) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多只能同时测试3个模型"
        )
    
    # 验证模型是否存在且可用
    results = {}
    for model_name in models_to_test:
        model = db.query(Model).filter(
            Model.name == model_name,
            Model.is_available == True
        ).first()
        
        if not model:
            results[model_name] = {
                "error": "模型不存在或不可用"
            }
            continue
        
        if model.status != "active":
            results[model_name] = {
                "error": "模型未加载"
            }
            continue
        
        # TODO: 调用实际的模型推理API
        # 这里先返回模拟结果
        results[model_name] = {
            "output": f"这是 {model.display_name} 对 '{input_text}' 的回复",
            "model_info": {
                "display_name": model.display_name,
                "parameters": model.parameters,
                "model_type": model.model_type
            }
        }
    
    # 保存测试记录
    test_record = ModelTest(
        user_id=current_user.id,
        test_name=f"模型对比测试 - {len(models_to_test)}个模型",
        models_tested=json.dumps(models_to_test),
        input_data=input_text,
        results=json.dumps(results),
        is_streaming=is_streaming
    )
    db.add(test_record)
    db.commit()
    
    return {
        "test_id": test_record.id,
        "results": results
    }

@router.get("/test/history", responses={401: {"model": ErrorResponse}})
async def get_test_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """获取用户的模型测试历史
    
    作用：
    - 分页返回当前用户的模型测试记录列表。
    
    触发链路：
    - 用户在测试历史页面查看过往测试记录。
    
    参数：
    - limit：每页记录数，默认 10。
    - offset：偏移量，默认 0。
    - db/current_user：依赖注入。
    
    返回：
    - 200 + 测试记录列表（包含 id、test_name、models_tested、input_data、results、created_at）。
    
    注意：
    - 按创建时间倒序排列；JSON 字段已解析为对象。
    """
    tests = db.query(ModelTest).filter(
        ModelTest.user_id == current_user.id
    ).order_by(ModelTest.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "id": test.id,
            "test_name": test.test_name,
            "models_tested": json.loads(test.models_tested),
            "input_data": test.input_data,
            "results": json.loads(test.results),
            "created_at": test.created_at
        }
        for test in tests
    ]

@router.post("/upload-image", responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传图片用于模型测试
    
    作用：
    - 接收图片文件上传，保存到本地并返回访问 URL。
    
    触发链路：
    - 用户在模型测试页面选择图片文件上传。
    
    参数：
    - file：上传的图片文件（通过 multipart/form-data）。
    - current_user：当前用户依赖注入。
    
    返回：
    - 200 + { filename, file_path, url }。
    
    注意：
    - 仅接受 image/* 类型文件；文件名使用 UUID 避免冲突；需确保 uploads/images 目录存在。
    """
    # 检查文件类型
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能上传图片文件"
        )
    
    # 创建上传目录
    upload_dir = "uploads/images"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件
    import uuid
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {
        "filename": unique_filename,
        "file_path": file_path,
        "url": f"/uploads/images/{unique_filename}"
    }

# 添加新模型
@router.post("/add", responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def add_model(
    model_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加新模型
    
    作用：
    - 在系统中注册新的模型记录，供后续加载和测试使用。
    
    触发链路：
    - 管理员在模型管理页面添加新模型。
    
    参数：
    - model_data：包含 name、display_name、model_path、model_type、description、parameters 的字典。
    - db/current_user：依赖注入。
    
    返回：
    - 200 + { id, name, display_name, message }。
    
    注意：
    - 需要管理员权限；model_type 默认为 "base"；parameters 以字符串形式存储。
    """
    model = Model(
        name=model_data["name"],
        display_name=model_data["display_name"],
        model_path=model_data["model_path"],
        model_type=model_data.get("model_type", "base"),
        description=model_data.get("description", ""),
        parameters=model_data.get("parameters", ""),
        created_by=current_user.id
    )
    
    db.add(model)
    db.commit()
    db.refresh(model)
    
    return {
        "id": model.id,
        "name": model.name,
        "display_name": model.display_name,
        "message": "模型添加成功"
    } 