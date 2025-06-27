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
    SystemPromptCreate, SystemPromptResponse, SystemPromptUpdate
)

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
    user_id: int,
    db: Session = Depends(get_db)
):
    """创建新的聊天会话"""
    session = ChatSession(
        user_id=user_id,
        title=session_data.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """获取用户的聊天会话列表"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取特定聊天会话及其消息"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
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
    user_id: int,
    db: Session = Depends(get_db)
):
    """更新聊天会话"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
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
    user_id: int,
    db: Session = Depends(get_db)
):
    """删除聊天会话"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    db.delete(session)
    db.commit()
    return {"message": "聊天会话已删除"}

# 聊天消息
@router.post("/messages", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """发送聊天消息"""
    # 如果没有指定会话，创建新会话
    if not message_data.session_id:
        session = ChatSession(user_id=user_id, title="新对话")
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
    else:
        session_id = message_data.session_id
        # 验证会话属于当前用户
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
    
    # 保存用户消息
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content,
        model_name=message_data.model_name
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # TODO: 这里应该调用实际的模型API生成回复
    # 现在先返回一个模拟回复
    assistant_content = f"这是对'{message_data.content}'的模拟回复"
    
    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=assistant_content,
        model_name=message_data.model_name,
        is_streaming=message_data.is_streaming
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return assistant_message

@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """导出聊天会话为txt文件"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
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
    user_id: int,
    db: Session = Depends(get_db)
):
    """创建系统提示词"""
    # 如果设置为默认，取消其他默认设置
    if prompt_data.is_default:
        db.query(SystemPrompt).filter(SystemPrompt.is_default == True).update(
            {"is_default": False}
        )
    
    prompt = SystemPrompt(
        name=prompt_data.name,
        content=prompt_data.content,
        is_default=prompt_data.is_default,
        created_by=user_id
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

@router.get("/system-prompts", response_model=List[SystemPromptResponse])
async def get_system_prompts(db: Session = Depends(get_db)):
    """获取所有系统提示词"""
    prompts = db.query(SystemPrompt).order_by(
        SystemPrompt.is_default.desc(),
        SystemPrompt.created_at.desc()
    ).all()
    return prompts

@router.put("/system-prompts/{prompt_id}", response_model=SystemPromptResponse)
async def update_system_prompt(
    prompt_id: int,
    prompt_data: SystemPromptUpdate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """更新系统提示词"""
    prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统提示词不存在"
        )
    
    if prompt_data.name:
        prompt.name = prompt_data.name
    if prompt_data.content:
        prompt.content = prompt_data.content
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
    user_id: int,
    db: Session = Depends(get_db)
):
    """删除系统提示词"""
    prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统提示词不存在"
        )
    
    db.delete(prompt)
    db.commit()
    return {"message": "系统提示词已删除"} 