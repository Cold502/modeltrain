from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 聊天消息
class ChatMessageCreate(BaseModel):
    session_id: Optional[int] = None
    content: str
    role: str = "user"  # user, assistant, system
    model_name: Optional[str] = None
    is_streaming: bool = False

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    model_name: Optional[str]
    is_streaming: bool
    created_at: datetime

    class Config:
        from_attributes = True

# 聊天会话
class ChatSessionCreate(BaseModel):
    title: Optional[str] = "新对话"

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None

# 系统提示词
class SystemPromptCreate(BaseModel):
    name: str
    content: str
    description: Optional[str] = None
    format_type: str = "openai"  # openai, ollama, custom
    category: str = "general"
    is_default: bool = False

class SystemPromptResponse(BaseModel):
    id: int
    name: str
    content: str
    description: Optional[str]
    format_type: str
    category: str
    is_default: bool
    is_system: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class SystemPromptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    format_type: Optional[str] = None
    category: Optional[str] = None
    is_default: Optional[bool] = None

# 系统提示词转换请求
class PromptConvertRequest(BaseModel):
    content: str
    source_format: str  # openai, ollama, custom
    target_format: str  # openai, ollama, custom

class PromptConvertResponse(BaseModel):
    converted_content: str
    format_info: dict

# 流式聊天响应
class StreamChatResponse(BaseModel):
    type: str  # "message", "end", "error"
    content: str
    session_id: Optional[int] = None
    message_id: Optional[int] = None 