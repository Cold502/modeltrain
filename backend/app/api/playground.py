from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.model_config import ModelConfig as ModelConfigModel
from app.llm_core.llm_client import LLMClient

router = APIRouter()

@router.post("/playground/chat")
async def playground_chat(
    request: dict,  # {"model_config_id": str, "messages": List[dict]}
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """模型测试聊天（普通模式）- 内部调用chat API"""
    # 直接使用chat API的逻辑
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

@router.post("/playground/chat/stream")
async def playground_chat_stream(
    request: dict,  # {"model_config_id": str, "messages": List[dict]}
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """模型测试聊天（流式模式）- 内部调用chat API"""
    # 直接使用chat API的逻辑
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