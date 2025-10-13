from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
from app.schemas.common import ErrorResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 聊天会话管理
@router.post("/sessions", response_model=ChatSessionResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def create_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的聊天会话

    作用：
    - 为当前用户创建一条新的聊天会话记录，返回会话基础信息。

    触发链路：
    - 前端点击“新建对话” → 提交标题等必要信息 → 写入数据库 → 返回 `ChatSessionResponse`。

    参数：
    - session_data：请求体（会话标题等）。
    - db：数据库会话。
    - current_user：当前认证用户（依赖注入）。

    返回：
    - 200 + `ChatSessionResponse`。

    注意：
    - 会话归属设置为当前用户，避免跨用户访问。
    """
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse], responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """获取用户的聊天会话列表

    作用：
    - 分页返回当前用户的会话列表，按最近更新时间倒序。

    参数：
    - limit：每页数量（默认 20）。
    - offset：偏移量（默认 0）。
    - db/current_user：依赖注入。

    返回：
    - 200 + `List[ChatSessionResponse]`。

    注意：
    - 仅返回当前用户自己的会话。
    """
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit).all()
        return sessions
    except Exception as e:
        logger.error(f"获取会话列表时出现错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话列表失败"
        )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse, responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取特定聊天会话及其消息

    作用：
    - 返回指定会话及其按时间升序排列的消息列表。

    参数：
    - session_id：会话 ID。
    - db/current_user：依赖注入。

    返回：
    - 200 + `ChatSessionResponse`（包含 messages）。

    注意：
    - 仅允许访问当前用户自己的会话，未找到则返回 404。
    """
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
@router.post("/messages", response_model=ChatMessageResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def send_message(
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送聊天消息

    作用：
    - 在指定会话（或自动创建新会话）中保存一条用户/系统/助手消息。

    触发链路：
    - 前端发送消息 → 若未提供会话 ID 则先创建会话 → 校验会话归属 → 持久化消息。

    参数：
    - message_data：消息请求体（role, content, model_name, is_streaming, session_id）。
    - db/current_user：依赖注入。

    返回：
    - 200 + `ChatMessageResponse`（新消息的持久化结果）。

    注意：
    - 仅允许向当前用户自己的会话写入；否则返回 404。
    - is_streaming 仅标记是否使用流式返回，具体推理由上层调用控制。
    """
    logger.info(f"收到消息保存请求，用户ID: {current_user.id}")
    # 用户ID已在上面记录
    
    # 如果没有指定会话，创建新会话
    if not message_data.session_id:
        logger.debug("创建新会话")
        session = ChatSession(user_id=current_user.id, title="新对话")
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
        logger.debug(f"新会话ID: {session_id}")
    else:
        session_id = message_data.session_id
        logger.debug(f"使用现有会话ID: {session_id}")
        # 验证会话属于当前用户
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            logger.warning(f"会话不存在或权限不足: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
    
    # 保存消息（支持用户指定role）
    logger.debug(f"保存消息到会话 {session_id}")
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
    logger.info(f"消息保存成功，ID: {message.id}")
    
    return message

@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出聊天会话为 txt 文件

    作用：
    - 将指定会话与消息渲染为纯文本内容，返回下载响应。

    参数：
    - session_id：会话 ID。
    - db/current_user：依赖注入。

    返回：
    - 200 + 文本下载（Content-Disposition: attachment）。

    注意：
    - 仅允许导出当前用户自己的会话；大体量时应考虑分页/流式输出。
    """
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
    
    # 特别保护"系统通用助手"
    if prompt.name == "系统通用助手":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除系统通用助手提示词"
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
                    # 为了遵循 SSE 规范并保留原始换行，将内容按行切分并为每行添加 data: 前缀
                    text = str(chunk)
                    for subline in text.splitlines():
                        yield f"data: {subline}\n"
                    # 以空行结尾，表示一个完整事件
                    yield "\n"
            
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