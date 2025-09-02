from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import os

from app.database import SessionLocal
from app.models.model import Model, ModelTest
from app.schemas.user import UserResponse
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 模型管理
@router.get("/list")
async def get_models(db: Session = Depends(get_db)):
    """获取所有可用模型列表"""
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

@router.post("/load/{model_id}")
async def load_model(model_id: int, db: Session = Depends(get_db)):
    """加载模型到VLLM"""
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

@router.post("/unload/{model_id}")
async def unload_model(model_id: int, db: Session = Depends(get_db)):
    """卸载模型"""
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
@router.post("/test")
async def test_models(
    test_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试多个模型对比"""
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

@router.get("/test/history")
async def get_test_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """获取用户的模型测试历史"""
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

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传图片用于模型测试"""
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
@router.post("/add")
async def add_model(
    model_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加新模型"""
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