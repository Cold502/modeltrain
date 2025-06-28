from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ModelProvider(Base):
    __tablename__ = "model_providers"
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    api_url = Column(String(500), nullable=False)
    description = Column(Text)
    icon_url = Column(String(500))
    status = Column(Integer, default=1)  # 1: 启用, 0: 禁用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # 关系
    model_configs = relationship("ModelConfig", back_populates="provider")
    provider_models = relationship("ProviderModel", back_populates="provider")

class ModelConfig(Base):
    __tablename__ = "model_configs"
    
    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)  # 默认用户
    provider_id = Column(String(100), ForeignKey("model_providers.id"), nullable=False, index=True)
    provider_name = Column(String(200), nullable=False)
    endpoint = Column(String(500), nullable=False)
    api_key = Column(Text)
    model_id = Column(String(200), nullable=False)
    model_name = Column(String(200), nullable=False)
    type = Column(String(50), default="text")  # text, vision
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=8192)
    status = Column(Integer, default=1)  # 1: 启用, 0: 禁用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="model_configs")
    provider = relationship("ModelProvider", back_populates="model_configs")

class ModelPlaygroundChat(Base):
    __tablename__ = "model_playground_chats"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String, nullable=False, index=True)
    model_config_id = Column(String(100), ForeignKey("model_configs.id"))
    role = Column(String, nullable=False)  # user, assistant, error
    content = Column(Text, nullable=False)
    thinking = Column(Text, nullable=True)  # 推理过程
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User")
    model_config = relationship("ModelConfig") 

class ProviderModel(Base):
    __tablename__ = "provider_models"
    
    id = Column(String(200), primary_key=True)  # provider_id + model_id
    provider_id = Column(String(100), ForeignKey("model_providers.id"), nullable=False, index=True)
    model_id = Column(String(200), nullable=False)
    model_name = Column(String(200), nullable=False)
    size = Column(Integer)  # 模型大小（字节）
    description = Column(Text)
    is_vision = Column(Boolean, default=False)  # 是否为视觉模型
    status = Column(Integer, default=1)  # 1: 可用, 0: 不可用
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # 关系
    provider = relationship("ModelProvider", back_populates="provider_models") 