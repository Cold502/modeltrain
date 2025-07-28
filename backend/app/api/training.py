from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import os
import asyncio
import subprocess
from datetime import datetime

from app.database import SessionLocal
from app.models.training import Dataset, TrainingConfig, TrainingTask
from app.schemas.training import (
    DatasetCreate, DatasetResponse,
    TrainingConfigCreate, TrainingConfigResponse,
    TrainingTaskCreate, TrainingTaskResponse
)

router = APIRouter()

# SwanLab 配置和进程管理
SWANLAB_CONFIG_FILE = "swanlab_config.json"
SWANLAB_PROCESS = None

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

import subprocess
import json
import os
import requests
from pathlib import Path

# SwanLab 配置存储
SWANLAB_CONFIG_FILE = "swanlab_config.json"
SWANLAB_PROCESS = None

def load_swanlab_config():
    """加载SwanLab配置"""
    if os.path.exists(SWANLAB_CONFIG_FILE):
        with open(SWANLAB_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "host": "localhost",
        "port": 5092,
        "data_dir": "./swanlab_data",
        "project_name": "modeltrain"
    }

def save_swanlab_config(config):
    """保存SwanLab配置"""
    with open(SWANLAB_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def check_swanlab_status():
    """检查SwanLab服务状态"""
    global SWANLAB_PROCESS
    if SWANLAB_PROCESS and SWANLAB_PROCESS.poll() is None:
        return "running"
    return "stopped"

@router.get("/swanlab")
async def get_swanlab_info():
    """获取SwanLab信息"""
    config = load_swanlab_config()
    status = check_swanlab_status()
    
    # 模拟项目数据
    projects = []
    if status == "running":
        projects = [
            {
                "name": "modeltrain",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "experiments": []
            }
        ]
    
    return {
        "status": status,
        "url": f"http://{config['host']}:{config['port']}",
        "projects": projects,
        "config": config
    }


def is_conda_env():
    # 一般 conda 会设置 CONDA_PREFIX 环境变量，base环境有时也会有，但路径不同
    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    if not conda_prefix:
        return False
    # 判断是不是base环境
    # base环境通常路径中包含 'base'，虚拟环境一般不是
    return "base" not in conda_prefix.lower()


@router.post("/swanlab/start")
async def start_swanlab(config: dict):
    global SWANLAB_PROCESS

    if check_swanlab_status() == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SwanLab服务已在运行"
        )

    try:
        data_dir = config.get("data_dir", "./swanlab_data")
        os.makedirs(data_dir, exist_ok=True)

        host = config.get("host", "127.0.0.1")
        port = str(config.get("port", 5092))

        if is_conda_env():
            # conda 虚拟环境，直接执行 swanlab 命令
            cmd = [
                "swanlab", "watch",
                "-h", host,
                "-p", port,
                "--logdir", data_dir
            ]
        else:
            # base 环境，用 python -m 方式启动
            cmd = [
                sys.executable, "-m", "swanlab", "watch",
                "-h", host,
                "-p", port,
                "--logdir", data_dir
            ]

        print(f"启动SwanLab命令: {' '.join(cmd)}")

        SWANLAB_PROCESS = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 等待一小段时间，检查启动是否成功
        await asyncio.sleep(2)

        if SWANLAB_PROCESS.poll() is not None:
            stdout, stderr = SWANLAB_PROCESS.communicate()
            error_msg = stderr if stderr else stdout
            print(f"SwanLab启动失败，错误信息: {error_msg}")
            raise Exception(f"SwanLab进程启动失败: {error_msg}")

        save_swanlab_config(config)
        return {"message": "SwanLab服务启动成功", "status": "starting"}

    except Exception as e:
        print(f"启动SwanLab时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动SwanLab失败: {str(e)}"
        )
@router.post("/swanlab/stop")
async def stop_swanlab():
    """停止SwanLab服务"""
    global SWANLAB_PROCESS
    
    if SWANLAB_PROCESS and SWANLAB_PROCESS.poll() is None:
        SWANLAB_PROCESS.terminate()
        SWANLAB_PROCESS.wait()
        SWANLAB_PROCESS = None
    
    return {"message": "SwanLab服务已停止"}

@router.post("/swanlab/config")
async def save_swanlab_config_api(config: dict):
    """保存SwanLab配置"""
    try:
        save_swanlab_config(config)
        return {"message": "配置保存成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}"
        )

@router.post("/swanlab/test")
async def test_swanlab_connection(config: dict):
    """测试SwanLab连接"""
    try:
        import requests
        url = f"http://{config.get('host', 'localhost')}:{config.get('port', 5092)}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return {"message": "连接测试成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="连接失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"连接测试失败: {str(e)}"
        )

@router.post("/swanlab/projects")
async def create_swanlab_project(project: dict):
    """创建SwanLab项目"""
    try:
        # 这里应该调用SwanLab API创建项目
        # 目前返回模拟数据
        return {
            "message": "项目创建成功",
            "project": {
                "name": project["name"],
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}"
        )

@router.delete("/swanlab/projects/{project_name}")
async def delete_swanlab_project(project_name: str):
    """删除SwanLab项目"""
    try:
        # 这里应该调用SwanLab API删除项目
        return {"message": f"项目 {project_name} 删除成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除项目失败: {str(e)}"
        )

@router.get("/swanlab/projects")
async def get_swanlab_projects():
    """获取SwanLab项目列表"""
    status = check_swanlab_status()
    if status != "running":
        return []
    
    # 模拟项目数据
    return [
        {
            "name": "modeltrain",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "experiments": []
        }
    ] 