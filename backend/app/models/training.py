from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    format_type = Column(String(50))  # json, jsonl, csv等
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TrainingConfig(Base):
    __tablename__ = "training_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    config_data = Column(JSON, nullable=False)  # 存储完整的训练配置
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TrainingTask(Base):
    __tablename__ = "training_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_name = Column(String(255), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    config_id = Column(Integer, ForeignKey("training_configs.id"))
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    log_file = Column(String(500))
    output_dir = Column(String(500))
    swanlab_url = Column(String(500))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    dataset = relationship("Dataset")
    config = relationship("TrainingConfig") 