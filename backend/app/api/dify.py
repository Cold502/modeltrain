"""
Dify API代理
提供知识库列表、工作流列表、对话和工作流执行功能
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
import httpx
import json
import logging
import os
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_TIMEOUT = 60


class DifyChatRequest(BaseModel):
    """Dify对话请求"""
    query: str
    conversation_id: Optional[str] = None
    dataset_ids: Optional[List[str]] = None
    user: Optional[str] = None


class DifyWorkflowRequest(BaseModel):
    """Dify工作流请求"""
    inputs: Dict[str, Any]
    user: Optional[str] = None


@router.get("/health")
async def check_dify_health():
    """
    检查Dify服务健康状态
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DIFY_API_URL}/console/api/setup")
            if response.status_code == 200:
                return {
                    "status": "running",
                    "api_url": DIFY_API_URL,
                    "message": "Dify服务正常"
                }
            else:
                return {
                    "status": "error",
                    "api_url": DIFY_API_URL,
                    "message": f"Dify服务响应异常: {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "stopped",
            "api_url": DIFY_API_URL,
            "message": f"无法连接到Dify服务: {str(e)}"
        }


@router.get("/datasets")
async def get_datasets(
    page: int = 1,
    limit: int = 20,
    keyword: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    获取知识库列表
    
    Args:
        page: 页码
        limit: 每页数量
        keyword: 搜索关键词
    """
    try:
        params = {
            "page": page,
            "limit": limit
        }
        if keyword:
            params["keyword"] = keyword
        
        async with httpx.AsyncClient(timeout=DIFY_TIMEOUT) as client:
            response = await client.get(
                f"{DIFY_API_URL}/v1/datasets",
                params=params,
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # 提取id和name，简化返回
            datasets = []
            for item in data.get("data", []):
                datasets.append({
                    "id": item["id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "document_count": item.get("document_count", 0),
                    "word_count": item.get("word_count", 0)
                })
            
            return {
                "datasets": datasets,
                "total": data.get("total", 0),
                "page": data.get("page", page),
                "has_more": data.get("has_more", False)
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Dify API错误: {e}")
    except Exception as e:
        logger.error(f"获取知识库列表异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def get_workflows(
    current_user: User = Depends(get_current_user)
):
    """
    获取工作流列表
    注意：Dify API可能没有直接的获取所有workflows的接口
    这里返回一个提示，让用户在Dify界面创建后手动配置
    """
    # TODO: 如果Dify有工作流列表API，在这里实现
    # 目前Dify的workflow需要通过app_id来执行，所以需要先在Dify中创建
    return {
        "message": "请在Dify控制台创建工作流应用，然后使用app_id进行调用",
        "workflows": []
    }


@router.post("/chat")
async def chat_with_dify(
    request: DifyChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    通过Dify进行对话（支持RAG）
    
    Args:
        query: 用户问题
        conversation_id: 会话ID（可选，用于多轮对话）
        dataset_ids: 知识库ID列表（可选）
        user: 用户标识（可选）
    """
    try:
        user_id = request.user or f"user_{current_user.id}"
        
        payload = {
            "inputs": {},
            "query": request.query,
            "response_mode": "streaming",
            "user": user_id,
            "files": []
        }
        
        if request.conversation_id:
            payload["conversation_id"] = request.conversation_id
        
        # 如果指定了知识库，添加到inputs
        if request.dataset_ids:
            payload["inputs"]["dataset_ids"] = request.dataset_ids
        
        async def generate():
            async with httpx.AsyncClient(timeout=DIFY_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{DIFY_API_URL}/v1/chat-messages",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {DIFY_API_KEY}",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip():
                                yield f"data: {data}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Dify对话失败: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Dify API错误: {e}")
    except Exception as e:
        logger.error(f"Dify对话异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{app_id}/run")
async def run_workflow(
    app_id: str,
    request: DifyWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """
    执行Dify工作流
    
    Args:
        app_id: Dify工作流应用ID
        inputs: 工作流输入参数
        user: 用户标识
    """
    try:
        user_id = request.user or f"user_{current_user.id}"
        
        payload = {
            "inputs": request.inputs,
            "response_mode": "streaming",
            "user": user_id
        }
        
        async def generate():
            async with httpx.AsyncClient(timeout=DIFY_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{DIFY_API_URL}/v1/workflows/run",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {DIFY_API_KEY}",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip():
                                yield f"data: {data}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"执行工作流失败: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Dify API错误: {e}")
    except Exception as e:
        logger.error(f"执行工作流异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    获取会话历史消息
    """
    try:
        async with httpx.AsyncClient(timeout=DIFY_TIMEOUT) as client:
            response = await client.get(
                f"{DIFY_API_URL}/v1/messages",
                params={
                    "conversation_id": conversation_id,
                    "limit": limit
                },
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}"
                }
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPStatusError as e:
        logger.error(f"获取会话历史失败: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Dify API错误: {e}")
    except Exception as e:
        logger.error(f"获取会话历史异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))
