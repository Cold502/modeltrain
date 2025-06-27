from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.sql import func
from app.database import Base

class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    model_path = Column(String(500), nullable=False)
    model_type = Column(String(100))  # base, lora, full等
    status = Column(String(50), default="inactive")  # active, inactive, loading, error
    is_available = Column(Boolean, default=True)
    description = Column(Text)
    parameters = Column(String(100))  # 7B, 13B等
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ModelTest(Base):
    __tablename__ = "model_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_name = Column(String(255), nullable=False)
    models_tested = Column(Text)  # JSON格式存储测试的模型列表
    input_data = Column(Text, nullable=False)
    results = Column(Text)  # JSON格式存储测试结果
    is_streaming = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 