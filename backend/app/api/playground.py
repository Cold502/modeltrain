from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.model_config import ModelConfig as ModelConfigModel
from app.llm_core.llm_client import LLMClient
from app.schemas.common import ErrorResponse
from app.utils.auth import get_current_user
from app.models.user import User

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/playground/chat", responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def playground_chat(
    request: dict,  # {"model_config_id": str, "messages": List[dict]}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """模型测试聊天（普通模式）
    
    作用：
    - 在 playground 环境中测试指定模型的对话能力，返回完整响应。
    
    触发链路：
    - 用户在 playground 页面提交测试请求。
    
    参数：
    - request：包含 model_config_id（模型配置 ID）和 messages（对话消息列表）的字典。
    - db/current_user：依赖注入。
    
    返回：
    - 200 + { response }（包含思维链的完整响应文本）。
    
    注意：
    - 支持思维链（CoT）推理；内部调用 LLMClient 的 get_response_with_cot 方法。
    """
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

@router.post("/playground/chat/stream", responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def playground_chat_stream(
    request: dict,  # {"model_config_id": str, "messages": List[dict]}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """模型测试聊天（流式模式）
    
    作用：
    - 在 playground 环境中测试指定模型的对话能力，以流式方式返回响应。
    
    触发链路：
    - 用户在 playground 页面启用流式模式提交测试请求。
    
    参数：
    - request：包含 model_config_id（模型配置 ID）和 messages（对话消息列表）的字典。
    - db/current_user：依赖注入。
    
    返回：
    - 200 + Server-Sent Events 流（text/event-stream）。
    
    注意：
    - 使用 SSE 格式流式输出；包含 CORS 头部；发送 [DONE] 标记结束流。
    """
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
            logger.error(f"流式响应生成异常: {str(e)}")
            logger.error(traceback.format_exc())
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