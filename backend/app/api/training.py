from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import os
import asyncio
from datetime import datetime

from app.database import SessionLocal
from app.models.training import Dataset, TrainingConfig, TrainingTask
from app.schemas.training import (
    DatasetCreate, DatasetResponse,
    TrainingConfigCreate, TrainingConfigResponse,
    TrainingTaskCreate, TrainingTaskResponse
)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/datasets", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """上传训练数据集"""
    allowed_formats = ['.json', '.jsonl', '.csv', '.txt']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式，支持的格式: {', '.join(allowed_formats)}"
        )
    
    upload_dir = "uploads/datasets"
    os.makedirs(upload_dir, exist_ok=True)
    
    import uuid
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    file_size = os.path.getsize(file_path)
    
    dataset = Dataset(
        name=name or file.filename,
        description=description,
        file_path=file_path,
        file_size=file_size,
        format_type=file_extension[1:],
        uploaded_by=user_id
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return dataset

@router.get("/datasets", response_model=List[DatasetResponse])
async def get_datasets(db: Session = Depends(get_db)):
    """获取数据集列表"""
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return datasets

@router.post("/tasks", response_model=TrainingTaskResponse)
async def create_training_task(
    task_data: TrainingTaskCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """创建训练任务"""
    dataset = db.query(Dataset).filter(Dataset.id == task_data.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在"
        )
    
    output_dir = f"outputs/training/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_data.name}"
    os.makedirs(output_dir, exist_ok=True)
    
    task = TrainingTask(
        name=task_data.name,
        model_name=task_data.model_name,
        dataset_id=task_data.dataset_id,
        config_id=task_data.config_id,
        output_dir=output_dir,
        created_by=user_id
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task

@router.get("/tasks", response_model=List[TrainingTaskResponse])
async def get_training_tasks(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取训练任务列表"""
    tasks = db.query(TrainingTask).filter(
        TrainingTask.created_by == user_id
    ).order_by(TrainingTask.created_at.desc()).all()
    return tasks

@router.post("/tasks/{task_id}/start")
async def start_training(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """启动训练任务"""
    task = db.query(TrainingTask).filter(
        TrainingTask.id == task_id,
        TrainingTask.created_by == user_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练任务不存在"
        )
    
    task.status = "running"
    task.started_at = datetime.now()
    db.commit()
    
    return {"message": "训练任务已启动", "task_id": task.id}

@router.get("/swanlab")
async def get_swanlab_info():
    """获取SwanLab信息"""
    return {
        "status": "available",
        "url": "http://localhost:5092",
        "projects": [{
            "name": "modeltrain",
            "url": "http://localhost:5092/project/modeltrain"
        }]
    } 