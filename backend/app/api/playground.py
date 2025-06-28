from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import uuid
from datetime import datetime

from app.database import get_db
from app.schemas.model_config import PlaygroundMessageRequest, PlaygroundStreamRequest
from app.models.model_config import ModelConfig as ModelConfigModel, ModelPlaygroundChat
from app.llm_core.llm_client import LLMClient

router = APIRouter(prefix="/playground", tags=["模型测试"])

@router.post("/chat")
async def playground_chat(
    request: PlaygroundMessageRequest,
    db: Session = Depends(get_db)
):
    """模型测试普通对话"""
    # 获取模型配置
    model_config = db.query(ModelConfigModel).filter(
        ModelConfigModel.id == request.model_config_id
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
        result = await llm_client.get_response_with_cot(request.messages)
        
        # 保存对话记录
        session_id = str(uuid.uuid4())
        
        # 保存用户消息
        if request.messages:
            last_message = request.messages[-1]
            user_chat = ModelPlaygroundChat(
                user_id=1,  # 使用默认用户ID
                session_id=session_id,
                model_config_id=request.model_config_id,
                role='user',
                content=json.dumps(last_message.get('content', ''))
            )
            db.add(user_chat)
        
        # 保存助手回复
        assistant_chat = ModelPlaygroundChat(
            user_id=1,  # 使用默认用户ID
            session_id=session_id,
            model_config_id=request.model_config_id,
            role='assistant',
            content=result['answer'],
            thinking=result['cot']
        )
        db.add(assistant_chat)
        db.commit()
        
        # 返回带推理链的响应
        response_text = result['answer']
        if result['cot']:
            response_text = f"<think>{result['cot']}</think>{result['answer']}"
        
        return {"response": response_text}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模型调用失败: {str(e)}"
        )

@router.post("/chat/stream")
async def playground_chat_stream(
    request: PlaygroundStreamRequest,
    db: Session = Depends(get_db)
):
    """模型测试流式对话"""
    # 获取模型配置
    model_config = db.query(ModelConfigModel).filter(
        ModelConfigModel.id == request.model_config_id
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
            stream = await llm_client.chat_stream(request.messages)
            
            session_id = str(uuid.uuid4())
            accumulated_content = ""
            accumulated_thinking = ""
            
            # 保存用户消息
            if request.messages:
                last_message = request.messages[-1]
                user_chat = ModelPlaygroundChat(
                    user_id=1,  # 使用默认用户ID
                    session_id=session_id,
                    model_config_id=request.model_config_id,
                    role='user',
                    content=json.dumps(last_message.get('content', ''))
                )
                db.add(user_chat)
                db.commit()
            
            # 流式输出
            async for chunk in stream:
                if chunk:
                    yield chunk
                    
                    # 累积内容用于保存
                    if '<think>' in chunk:
                        accumulated_thinking += chunk.replace('<think>', '')
                    elif '</think>' in chunk:
                        accumulated_thinking += chunk.replace('</think>', '')
                    else:
                        if accumulated_thinking and not chunk.startswith('<'):
                            accumulated_content += chunk
                        elif not accumulated_thinking:
                            accumulated_content += chunk
            
            # 保存助手回复
            assistant_chat = ModelPlaygroundChat(
                user_id=1,  # 使用默认用户ID
                session_id=session_id,
                model_config_id=request.model_config_id,
                role='assistant',
                content=accumulated_content,
                thinking=accumulated_thinking
            )
            db.add(assistant_chat)
            db.commit()
            
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/chat/history")
async def get_chat_history(
    session_id: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取对话历史"""
    query = db.query(ModelPlaygroundChat)
    
    if session_id:
        query = query.filter(ModelPlaygroundChat.session_id == session_id)
    
    chats = query.order_by(ModelPlaygroundChat.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": chat.id,
            "session_id": chat.session_id,
            "model_config_id": chat.model_config_id,
            "role": chat.role,
            "content": chat.content,
            "thinking": chat.thinking,
            "created_at": chat.created_at
        }
        for chat in chats
    ]

@router.delete("/chat/history/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """删除对话会话"""
    chats = db.query(ModelPlaygroundChat).filter(
        ModelPlaygroundChat.session_id == session_id
    ).all()
    
    for chat in chats:
        db.delete(chat)
    
    db.commit()
    return {"message": "对话会话删除成功"} 