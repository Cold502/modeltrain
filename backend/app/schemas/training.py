from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

# 数据集
class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None

class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    file_path: str
    file_size: Optional[int]
    format_type: Optional[str]
    uploaded_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

# 训练配置
class TrainingConfigCreate(BaseModel):
    name: str
    config_data: Dict[str, Any]

class TrainingConfigResponse(BaseModel):
    id: int
    name: str
    config_data: Dict[str, Any]
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# 训练任务
class TrainingTaskCreate(BaseModel):
    name: str
    model_name: str
    dataset_id: int
    config_id: Optional[int] = None
    config_data: Optional[Dict[str, Any]] = None

class TrainingTaskResponse(BaseModel):
    id: int
    name: str
    model_name: str
    dataset_id: int
    config_id: Optional[int]
    status: str
    progress: float
    log_file: Optional[str]
    output_dir: Optional[str]
    swanlab_url: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

# LlamaFactory训练配置
class LlamaFactoryConfig(BaseModel):
    # 基础配置
    stage: str = "sft"  # sft, rm, ppo, dpo
    model_name: str
    dataset: str
    template: str = "default"
    
    # 训练参数
    learning_rate: float = 5e-5
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    max_grad_norm: float = 1.0
    
    # LoRA配置
    finetuning_type: str = "lora"  # lora, full
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    lora_target: str = "q_proj,v_proj"
    
    # 输出配置
    output_dir: str
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    save_total_limit: int = 2
    
    # 其他配置
    fp16: bool = True
    do_eval: bool = True
    evaluation_strategy: str = "steps"
    load_best_model_at_end: bool = True
    
    # SwanLab配置
    use_swanlab: bool = True
    swanlab_project: str = "modeltrain" 