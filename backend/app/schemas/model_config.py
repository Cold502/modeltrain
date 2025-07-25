from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class ModelProviderBase(BaseModel):
    id: str
    name: str
    api_url: str = Field(alias="apiUrl")
    description: Optional[str] = None
    icon_url: Optional[str] = Field(None, alias="iconUrl")
    status: int = 1

    class Config:
        populate_by_name = True

class ModelProviderResponse(ModelProviderBase):
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(alias="updatedAt")
    
    class Config:
        from_attributes = True
        populate_by_name = True

class ModelConfigBase(BaseModel):
    provider_id: str = Field(..., alias="providerId")
    provider_name: str = Field(..., alias="providerName")
    endpoint: str
    api_key: Optional[str] = Field(None, alias="apiKey")
    model_id: str = Field(..., alias="modelId")
    model_name: str = Field(..., alias="modelName")
    type: str = "text"
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Temperature must be between 0.0 and 1.0")
    max_tokens: int = Field(8192, alias="maxTokens", ge=1, le=32768)
    top_p: float = Field(0.9, alias="topP", ge=0.0, le=1.0)
    top_k: float = Field(0.0, alias="topK", ge=0.0)
    status: int = 1

    class Config:
        populate_by_name = True

class ModelConfigCreate(ModelConfigBase):
    pass

class ModelConfigUpdate(ModelConfigBase):
    provider_id: Optional[str] = Field(None, alias="providerId")
    provider_name: Optional[str] = Field(None, alias="providerName")
    endpoint: Optional[str] = None
    model_id: Optional[str] = Field(None, alias="modelId")
    model_name: Optional[str] = Field(None, alias="modelName")

class ModelConfigResponse(BaseModel):
    id: str
    user_id: int = Field(alias="userId")
    provider_id: str = Field(alias="providerId")
    provider_name: str = Field(alias="providerName")
    endpoint: str
    api_key: Optional[str] = Field(alias="apiKey")
    model_id: str = Field(alias="modelId")
    model_name: str = Field(alias="modelName")
    type: str
    temperature: float
    max_tokens: int = Field(alias="maxTokens")
    top_p: float = Field(alias="topP")
    top_k: float = Field(alias="topK")
    status: int
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True

class ModelConfig(ModelConfigBase):
    id: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ModelPlaygroundChatBase(BaseModel):
    session_id: str
    model_config_id: str
    role: str
    content: str
    thinking: Optional[str] = None

class ModelPlaygroundChatCreate(ModelPlaygroundChatBase):
    pass

class ModelPlaygroundChat(ModelPlaygroundChatBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PlaygroundMessageRequest(BaseModel):
    model_config_id: str
    messages: List[dict]
    temperature: float = 0.7
    max_tokens: int = 8192

class PlaygroundStreamRequest(BaseModel):
    model_config_id: str
    messages: List[dict] 
    temperature: float = 0.7
    max_tokens: int = 8192
    stream: bool = True

class ModelBase(BaseModel):
    id: str
    provider_id: str = Field(alias="providerId")
    model_id: str = Field(alias="modelId")
    model_name: str = Field(alias="modelName")
    size: Optional[int] = None
    description: Optional[str] = None
    is_vision: bool = Field(False, alias="isVision")
    status: int = 1

    class Config:
        populate_by_name = True

class ModelResponse(ModelBase):
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True

class RefreshModelsRequest(BaseModel):
    endpoint: str
    provider_id: str = Field(alias="providerId")
    api_key: Optional[str] = Field(None, alias="apiKey")

    class Config:
        populate_by_name = True 