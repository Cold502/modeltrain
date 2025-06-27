from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models.model import Model
from app.schemas.model_schema import ModelCreate, ModelUpdate, ModelResponse

router = APIRouter()

# 数据库会话依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/models", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def create_model(model: ModelCreate, db: Session = Depends(get_db)):
    """
    创建一个新模型记录
    """
    db_model = db.query(Model).filter(Model.name == model.name).first()
    if db_model:
        raise HTTPException(status_code=400, detail="同名模型已存在")
    
    new_model = Model(**model.dict())
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return new_model

@router.get("/models", response_model=List[ModelResponse])
def get_all_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取所有模型列表
    """
    models = db.query(Model).offset(skip).limit(limit).all()
    return models

@router.put("/models/{model_id}", response_model=ModelResponse)
def update_model_info(model_id: int, model_update: ModelUpdate, db: Session = Depends(get_db)):
    """
    更新指定模型的信息
    """
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="模型未找到")
    
    update_data = model_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_model, key, value)
        
    db.commit()
    db.refresh(db_model)
    return db_model

@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_record(model_id: int, db: Session = Depends(get_db)):
    """
    删除一个模型记录
    """
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="模型未找到")
        
    db.delete(db_model)
    db.commit()
    return {"ok": True} 