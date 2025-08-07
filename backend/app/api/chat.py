from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio
from datetime import datetime

from app.database import SessionLocal
from app.models.chat import ChatSession, ChatMessage, SystemPrompt
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate,
    ChatMessageCreate, ChatMessageResponse,
    SystemPromptCreate, SystemPromptResponse, SystemPromptUpdate,
    PromptConvertRequest, PromptConvertResponse
)
from app.services.prompt_service import PromptService
from app.llm_core.llm_client import LLMClient
from app.models.model_config import ModelConfig as ModelConfigModel
from app.utils.auth import get_current_user
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 聊天会话管理
@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的聊天会话"""
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """获取用户的聊天会话列表"""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit).all()
        return sessions
    except Exception as e:
        print(f"获取会话列表时出现错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话列表失败"
        )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取特定聊天会话及其消息"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在或无权访问"
        )
    
    # 获取消息
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    session.messages = messages
    return session

@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: int,
    session_data: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新聊天会话"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    if session_data.title:
        session.title = session_data.title
    
    db.commit()
    db.refresh(session)
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除聊天会话"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在或无权访问"
        )
    
    db.delete(session)
    db.commit()
    return {"message": "聊天会话已删除"}

# 聊天消息
@router.post("/messages", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送聊天消息"""
    print(f"🔍 收到消息保存请求: {message_data}")
    print(f"🔍 用户ID: {current_user.id}")
    
    # 如果没有指定会话，创建新会话
    if not message_data.session_id:
        print("🔍 创建新会话...")
        session = ChatSession(user_id=current_user.id, title="新对话")
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
        print(f"🔍 新会话ID: {session_id}")
    else:
        session_id = message_data.session_id
        print(f"🔍 使用现有会话ID: {session_id}")
        # 验证会话属于当前用户
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            print(f"🔍 会话不存在或权限不足")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
    
    # 保存消息（支持用户指定role）
    print(f"🔍 保存消息到会话 {session_id}")
    message = ChatMessage(
        session_id=session_id,
        role=message_data.role,
        content=message_data.content,
        model_name=message_data.model_name,
        is_streaming=message_data.is_streaming
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    print(f"🔍 消息保存成功，ID: {message.id}")
    
    return message

@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出聊天会话为txt文件"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # 生成文本内容
    content = f"聊天会话：{session.title}\n"
    content += f"创建时间：{session.created_at}\n"
    content += "=" * 50 + "\n\n"
    
    for msg in messages:
        role_name = "用户" if msg.role == "user" else "助手"
        content += f"{role_name}（{msg.created_at}）：\n{msg.content}\n\n"
    
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=chat_{session_id}.txt"
        }
    )

# 系统提示词管理
@router.post("/system-prompts", response_model=SystemPromptResponse)
async def create_system_prompt(
    prompt_data: SystemPromptCreate,
    db: Session = Depends(get_db)
):
    """创建系统提示词"""
    # 使用默认用户ID，在实际应用中应该从JWT token中获取
    user_id = 1
    
    # 验证提示词格式
    validation = PromptService.validate_prompt_format(prompt_data.content, prompt_data.format_type)
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提示词格式验证失败: {', '.join(validation['errors'])}"
        )
    
    # 如果设置为默认，取消其他默认设置
    if prompt_data.is_default:
        db.query(SystemPrompt).filter(SystemPrompt.is_default == True).update(
            {"is_default": False}
        )
    
    prompt = SystemPrompt(
        name=prompt_data.name,
        content=prompt_data.content,
        description=prompt_data.description,
        format_type=prompt_data.format_type,
        category=prompt_data.category,
        is_default=prompt_data.is_default,
        created_by=user_id
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

@router.get("/system-prompts", response_model=List[SystemPromptResponse])
async def get_system_prompts(
    category: str = None,
    format_type: str = None,
    db: Session = Depends(get_db)
):
    """获取系统提示词列表"""
    query = db.query(SystemPrompt)
    
    if category:
        query = query.filter(SystemPrompt.category == category)
    
    if format_type:
        query = query.filter(SystemPrompt.format_type == format_type)
    
    prompts = query.order_by(
        SystemPrompt.is_default.desc(),
        SystemPrompt.created_at.desc()
    ).all()
    
    return prompts

@router.get("/system-prompts/predefined")
async def get_predefined_prompts():
    """获取预定义系统提示词模板"""
    return {
        "prompts": PromptService.get_predefined_prompts(),
        "categories": ["general", "coding", "translation", "creative", "academic", "business"],
        "formats": ["openai", "ollama", "custom"]
    }

@router.post("/system-prompts/predefined/{key}")
async def create_from_predefined(
    key: str,
    db: Session = Depends(get_db)
):
    """从预定义模板创建系统提示词"""
    user_id = 1
    
    predefined = PromptService.get_prompt_by_key(key)
    if not predefined:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预定义模板不存在"
        )
    
    # 检查是否已存在相同名称的提示词
    existing = db.query(SystemPrompt).filter(
        SystemPrompt.name == predefined["name"],
        SystemPrompt.created_by == user_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在相同名称的系统提示词"
        )
    
    prompt = SystemPrompt(
        name=predefined["name"],
        content=predefined["content"],
        description=predefined["description"],
        format_type=predefined["format_type"],
        category=predefined["category"],
        is_system=True,
        created_by=user_id
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

@router.put("/system-prompts/{prompt_id}", response_model=SystemPromptResponse)
async def update_system_prompt(
    prompt_id: int,
    prompt_data: SystemPromptUpdate,
    db: Session = Depends(get_db)
):
    """更新系统提示词"""
    user_id = 1
    
    prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统提示词不存在"
        )
    
    # 验证提示词格式（如果内容被修改）
    if prompt_data.content:
        format_type = prompt_data.format_type or prompt.format_type
        validation = PromptService.validate_prompt_format(prompt_data.content, format_type)
        if not validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"提示词格式验证失败: {', '.join(validation['errors'])}"
            )
    
    # 更新字段
    if prompt_data.name:
        prompt.name = prompt_data.name
    if prompt_data.content:
        prompt.content = prompt_data.content
    if prompt_data.description is not None:
        prompt.description = prompt_data.description
    if prompt_data.format_type:
        prompt.format_type = prompt_data.format_type
    if prompt_data.category:
        prompt.category = prompt_data.category
    if prompt_data.is_default is not None:
        if prompt_data.is_default:
            # 取消其他默认设置
            db.query(SystemPrompt).filter(SystemPrompt.is_default == True).update(
                {"is_default": False}
            )
        prompt.is_default = prompt_data.is_default
    
    db.commit()
    db.refresh(prompt)
    return prompt

@router.delete("/system-prompts/{prompt_id}")
async def delete_system_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """删除系统提示词"""
    user_id = 1
    
    prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统提示词不存在"
        )
    
    # 防止删除系统预定义提示词
    if prompt.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除系统预定义提示词"
        )
    
    db.delete(prompt)
    db.commit()
    return {"message": "系统提示词已删除"} 

@router.post("/system-prompts/convert", response_model=PromptConvertResponse)
async def convert_prompt_format(convert_request: PromptConvertRequest):
    """转换提示词格式"""
    try:
        result = PromptService.convert_format(
            convert_request.content,
            convert_request.source_format,
            convert_request.target_format
        )
        return PromptConvertResponse(
            converted_content=result["converted_content"],
            format_info=result["format_info"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"格式转换失败: {str(e)}"
        )

@router.post("/system-prompts/{prompt_id}/validate")
async def validate_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """验证系统提示词格式"""
    prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统提示词不存在"
        )
    
    validation = PromptService.validate_prompt_format(prompt.content, prompt.format_type)
    examples = PromptService.generate_example_usage(prompt.content, prompt.format_type)
    
    return {
        "validation": validation,
        "examples": examples,
        "prompt_info": {
            "id": prompt.id,
            "name": prompt.name,
            "format_type": prompt.format_type,
            "category": prompt.category
        }
    }

@router.post("/")
async def model_chat(
    request: dict,  # {"model_config_id": str, "messages": List[dict]}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """模型聊天（普通模式）"""
    model_config_id = request.get("model_config_id")
    messages = request.get("messages", [])
    
    # 获取模型配置
    model_config = db.query(ModelConfigModel).filter(
        ModelConfigModel.id == model_config_id
    ).first()
    
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型配置不存在"
        )
    
    # 创建LLM客户端
    llm_client = LLMClient({
        'provider_id': model_config.provider_id,
        'endpoint': model_config.endpoint,
        'api_key': model_config.api_key,
        'model_name': model_config.model_name,
        'temperature': model_config.temperature,
        'max_tokens': model_config.max_tokens,
        'top_p': model_config.top_p,
        'top_k': model_config.top_k
    })
    
    try:
        # 获取带推理链的响应
        result = await llm_client.get_response_with_cot(messages)
        
        # 构建完整响应（包含思维链）
        response_text = result['answer']
        if result['cot']:
            response_text = f"<think>{result['cot']}</think>{result['answer']}"
        
        return {"response": response_text}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模型调用失败: {str(e)}"
        )

@router.post("/stream")
async def model_chat_stream(
    request: dict,  # {"model_config_id": str, "messages": List[dict]}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """模型聊天（流式模式）"""
    model_config_id = request.get("model_config_id")
    messages = request.get("messages", [])
    
    # 获取模型配置
    model_config = db.query(ModelConfigModel).filter(
        ModelConfigModel.id == model_config_id
    ).first()
    
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型配置不存在"
        )
    
    # 创建LLM客户端
    llm_client = LLMClient({
        'provider_id': model_config.provider_id,
        'endpoint': model_config.endpoint,
        'api_key': model_config.api_key,
        'model_name': model_config.model_name,
        'temperature': model_config.temperature,
        'max_tokens': model_config.max_tokens,
        'top_p': model_config.top_p,
        'top_k': model_config.top_k
    })
    
    async def generate_stream():
        try:
            # 获取流式响应
            stream = await llm_client.chat_stream(messages)
            
            # 流式输出
            async for chunk in stream:
                if chunk:
                    # 使用正确的SSE格式
                    yield f"data: {chunk}\n\n"
            
            # 发送结束标记
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    ) 