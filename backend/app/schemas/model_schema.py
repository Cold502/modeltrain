from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ModelBase(BaseModel):
    name: str = Field(..., description="模型名称，唯一标识")
    display_name: Optional[str] = Field(None, description="用于显示的名称")
    description: Optional[str] = Field(None, description="模型描述")
    path: Optional[str] = Field(None, description="模型文件路径")
    status: str = Field("inactive", description="模型状态 (e.g., active, inactive, loading)")

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    status: Optional[str] = None

class ModelResponse(ModelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 