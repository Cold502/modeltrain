from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库配置
DATABASE_URL = "sqlite:///./modeltrain.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def create_tables():
    """创建所有数据库表"""
    from app.models import user, chat, training, model
    Base.metadata.create_all(bind=engine) 