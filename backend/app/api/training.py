import sys
import logging

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import os
import asyncio
import subprocess
from datetime import datetime

from ..database import SessionLocal
from ..models.training import Dataset, TrainingConfig, TrainingTask
from ..schemas.training import (
    DatasetCreate, DatasetResponse,
    TrainingConfigCreate, TrainingConfigResponse,
    TrainingTaskCreate, TrainingTaskResponse
)
from app.schemas.common import ErrorResponse
from app.utils.auth import get_current_user
from app.models.user import User

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

# SwanLab 配置和进程管理
SWANLAB_CONFIG_FILE = "swanlab_config.json"
SWANLAB_PROCESS = None

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

@router.post("/datasets", response_model=DatasetResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传训练数据集
    
    作用：
    - 接收训练数据文件上传，保存到本地并创建数据集记录。
    
    触发链路：
    - 用户在训练页面选择数据文件上传。
    
    参数：
    - file：上传的数据文件（支持 .json、.jsonl、.csv、.txt）。
    - name：数据集名称（可选，默认使用文件名）。
    - description：数据集描述（可选）。
    - db/current_user：依赖注入。
    
    返回：
    - 200 + `DatasetResponse`。
    
    注意：
    - 文件保存到 uploads/datasets 目录，使用 UUID 避免重名；记录文件大小和格式类型。
    """
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
        uploaded_by=current_user.id
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return dataset

@router.get("/datasets", response_model=List[DatasetResponse], responses={500: {"model": ErrorResponse}})
async def get_datasets(db: Session = Depends(get_db)):
    """获取数据集列表
    
    作用：
    - 返回系统中所有已上传的数据集信息。
    
    触发链路：
    - 前端训练页面加载数据集选择列表。
    
    参数：
    - db：数据库会话依赖注入。
    
    返回：
    - 200 + 数据集列表（按创建时间倒序）。
    
    注意：
    - 返回所有数据集，不区分用户；包含文件路径、大小、格式等信息。
    """
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return datasets

@router.post("/tasks", response_model=TrainingTaskResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def create_training_task(
    task_data: TrainingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建训练任务
    
    作用：
    - 基于指定数据集和配置创建新的训练任务记录。
    
    触发链路：
    - 用户在训练页面提交训练任务配置。
    
    参数：
    - task_data：包含 name、model_name、dataset_id、config_id 的任务配置。
    - db/current_user：依赖注入。
    
    返回：
    - 200 + `TrainingTaskResponse`。
    
    注意：
    - 验证数据集存在性；自动创建输出目录（按时间戳命名）；任务状态初始为 pending。
    """
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
        created_by=current_user.id
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task

@router.get("/tasks", response_model=List[TrainingTaskResponse], responses={401: {"model": ErrorResponse}})
async def get_training_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取训练任务列表
    
    作用：
    - 返回当前用户创建的所有训练任务记录。
    
    触发链路：
    - 前端训练任务管理页面加载任务列表。
    
    参数：
    - db/current_user：依赖注入。
    
    返回：
    - 200 + 训练任务列表（按创建时间倒序）。
    
    注意：
    - 仅返回当前用户创建的任务；包含任务状态、配置信息等。
    """
    tasks = db.query(TrainingTask).filter(
        TrainingTask.created_by == current_user.id
    ).order_by(TrainingTask.created_at.desc()).all()
    return tasks

@router.post("/tasks/{task_id}/start", responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
async def start_training(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动训练任务
    
    作用：
    - 将指定训练任务状态更新为运行中，并记录开始时间。
    
    触发链路：
    - 用户在任务列表页面点击"开始训练"按钮。
    
    参数：
    - task_id：要启动的训练任务 ID。
    - db/current_user：依赖注入。
    
    返回：
    - 200 + { message, task_id }。
    
    注意：
    - 仅允许启动当前用户自己的任务；状态更新为 running，记录 started_at 时间。
    """
    task = db.query(TrainingTask).filter(
        TrainingTask.id == task_id,
        TrainingTask.created_by == current_user.id
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

@router.get("/swanlab", responses={500: {"model": ErrorResponse}})
async def get_swanlab_info():
    """获取 SwanLab 信息
    
    作用：
    - 返回 SwanLab 服务状态、配置信息和项目列表。
    
    触发链路：
    - 前端训练监控页面加载 SwanLab 状态。
    
    参数：
    - 无直接参数。
    
    返回：
    - 200 + { status, url, projects, config }。
    
    注意：
    - 检查 SwanLab 进程状态；返回模拟项目数据（实际应调用 SwanLab API）。
    """
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


@router.post("/swanlab/start", responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def start_swanlab(config: dict):
    """启动 SwanLab 服务
    
    作用：
    - 根据配置启动 SwanLab 监控服务进程。
    
    触发链路：
    - 用户在训练监控页面点击"启动 SwanLab"按钮。
    
    参数：
    - config：包含 host、port、data_dir 的配置字典。
    
    返回：
    - 200 + { message, status }。
    
    注意：
    - 自动检测 conda 环境选择启动方式；创建数据目录；保存配置到文件。
    """
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

        logger.info(f"启动SwanLab命令: {' '.join(cmd)}")

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
            logger.error(f"SwanLab启动失败，错误信息: {error_msg}")
            raise Exception(f"SwanLab进程启动失败: {error_msg}")

        save_swanlab_config(config)
        return {"message": "SwanLab服务启动成功", "status": "starting"}

    except Exception as e:
        logger.error(f"启动SwanLab时发生异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动SwanLab失败: {str(e)}"
        )
@router.post("/swanlab/stop", responses={500: {"model": ErrorResponse}})
async def stop_swanlab():
    """停止 SwanLab 服务
    
    作用：
    - 终止当前运行的 SwanLab 服务进程。
    
    触发链路：
    - 用户在训练监控页面点击"停止 SwanLab"按钮。
    
    参数：
    - 无直接参数。
    
    返回：
    - 200 + { message }。
    
    注意：
    - 发送 SIGTERM 信号终止进程；等待进程完全退出。
    """
    global SWANLAB_PROCESS
    
    if SWANLAB_PROCESS and SWANLAB_PROCESS.poll() is None:
        SWANLAB_PROCESS.terminate()
        SWANLAB_PROCESS.wait()
        SWANLAB_PROCESS = None
    
    return {"message": "SwanLab服务已停止"}

@router.post("/swanlab/config", responses={500: {"model": ErrorResponse}})
async def save_swanlab_config_api(config: dict):
    """保存 SwanLab 配置
    
    作用：
    - 将 SwanLab 配置保存到本地配置文件。
    
    触发链路：
    - 用户在 SwanLab 配置页面提交配置表单。
    
    参数：
    - config：包含 host、port、data_dir、project_name 的配置字典。
    
    返回：
    - 200 + { message }。
    
    注意：
    - 配置保存到 swanlab_config.json 文件；使用 UTF-8 编码。
    """
    try:
        save_swanlab_config(config)
        return {"message": "配置保存成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}"
        )

@router.post("/swanlab/test", responses={400: {"model": ErrorResponse}})
async def test_swanlab_connection(config: dict):
    """测试 SwanLab 连接
    
    作用：
    - 测试指定配置下 SwanLab 服务的连接可用性。
    
    触发链路：
    - 用户在 SwanLab 配置页面点击"测试连接"按钮。
    
    参数：
    - config：包含 host、port 的配置字典。
    
    返回：
    - 200 + { message }。
    
    注意：
    - 发送 HTTP GET 请求测试连接；5 秒超时；返回连接状态。
    """
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

@router.post("/swanlab/projects", responses={500: {"model": ErrorResponse}})
async def create_swanlab_project(project: dict):
    """创建 SwanLab 项目
    
    作用：
    - 在 SwanLab 中创建新的监控项目。
    
    触发链路：
    - 用户在训练监控页面创建新项目。
    
    参数：
    - project：包含 name 的项目信息字典。
    
    返回：
    - 200 + { message, project }。
    
    注意：
    - 当前返回模拟数据；实际应调用 SwanLab API 创建项目。
    """
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

@router.delete("/swanlab/projects/{project_name}", responses={500: {"model": ErrorResponse}})
async def delete_swanlab_project(project_name: str):
    """删除 SwanLab 项目
    
    作用：
    - 删除指定的 SwanLab 监控项目。
    
    触发链路：
    - 用户在项目列表页面点击删除项目。
    
    参数：
    - project_name：要删除的项目名称。
    
    返回：
    - 200 + { message }。
    
    注意：
    - 当前返回模拟响应；实际应调用 SwanLab API 删除项目。
    """
    try:
        # 这里应该调用SwanLab API删除项目
        return {"message": f"项目 {project_name} 删除成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除项目失败: {str(e)}"
        )

@router.get("/swanlab/projects", responses={500: {"model": ErrorResponse}})
async def get_swanlab_projects():
    """获取 SwanLab 项目列表
    
    作用：
    - 返回 SwanLab 中的所有监控项目列表。
    
    触发链路：
    - 前端项目列表页面加载项目数据。
    
    参数：
    - 无直接参数。
    
    返回：
    - 200 + 项目列表（包含 name、status、created_at、updated_at、experiments）。
    
    注意：
    - 仅当 SwanLab 服务运行时返回数据；当前返回模拟项目数据。
    """
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