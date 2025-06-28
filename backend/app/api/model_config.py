from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import httpx
import asyncio

from app.database import get_db
from app.schemas.model_config import (
    ModelConfigCreate, ModelConfigUpdate,
    ModelConfigResponse, ModelProviderResponse, ModelResponse, RefreshModelsRequest,
    PlaygroundMessageRequest, PlaygroundStreamRequest
)
from app.models.model_config import ModelConfig as ModelConfigModel, ModelProvider as ModelProviderModel, ProviderModel
from app.llm_core.llm_client import get_model_providers, LLMClient

router = APIRouter(prefix="/model-config", tags=["模型配置"])

# 默认模型提供商
DEFAULT_PROVIDERS = [
    {
        "id": "ollama",
        "name": "Ollama ", 
        "api_url": "http://127.0.0.1:11434/api"
    },
    {
        "id": "vllm",
        "name": "VLLM ",
        "api_url": "http://127.0.0.1:8000/v1/"
    },
    {
        "id": "deepseek",
        "name": "DeepSeek", 
        "api_url": "https://api.deepseek.com/v1/"
    },
    {
        "id": "openai",
        "name": "OpenAI GPT", 
        "api_url": "https://api.openai.com/v1/"
    },
    {
        "id": "claude",
        "name": "Claude", 
        "api_url": "https://api.anthropic.com/v1/"
    },
    {
        "id": "tongyi",
        "name": "通义千问", 
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/"
    },
    {
        "id": "doubao",
        "name": "豆包", 
        "api_url": "https://ark.cn-beijing.volces.com/api/v3/"
    },
    {
        "id": "kimi",
        "name": "Kimi", 
        "api_url": "https://api.moonshot.cn/v1/"
    },
    {
        "id": "zhipu",
        "name": "智谱清言 GLM", 
        "api_url": "https://open.bigmodel.cn/api/paas/v4/"
    },
    {
        "id": "chatglm",
        "name": "ChatGLM", 
        "api_url": "https://open.bigmodel.cn/api/paas/v4/"
    },
    {
        "id": "gemini",
        "name": "Google Gemini", 
        "api_url": "https://generativelanguage.googleapis.com/v1/"
    },
    {
        "id": "wenxin",
        "name": "文心一言", 
        "api_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/"
    },
    {
        "id": "hunyuan",
        "name": "腾讯混元", 
        "api_url": "https://hunyuan.tencentcloudapi.com/"
    },
    {
        "id": "yi",
        "name": "零一万物 Yi", 
        "api_url": "https://api.lingyiwanwu.com/v1/"
    },
    {
        "id": "siliconflow",
        "name": "硅基流动", 
        "api_url": "https://api.siliconflow.cn/v1/"
    }
]

# 默认模型配置列表（按优先级排序）
DEFAULT_MODEL_CONFIGS = [
    # 1. Ollama 
    {
        "provider_id": "ollama",
        "provider_name": "Ollama",
        "endpoint": "http://127.0.0.1:11434/api",
        "api_key": "",
        "model_id": "qwen2.5:latest",
        "model_name": "Qwen2.5-7B",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 1
    },
    {
        "provider_id": "ollama",
        "provider_name": "Ollama",
        "endpoint": "http://127.0.0.1:11434/api",
        "api_key": "",
        "model_id": "llama3.2:latest",
        "model_name": "Llama3.2-3B",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 1
    },
    # 2. VLLM 
    {
        "provider_id": "vllm",
        "provider_name": "VLLM",
        "endpoint": "http://127.0.0.1:8000/v1/",
        "api_key": "",
        "model_id": "meta-llama/Llama-2-7b-chat-hf",
        "model_name": "Llama-2-7B-Chat",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 1
    },
    # 3. DeepSeek
    {
        "provider_id": "deepseek",
        "provider_name": "DeepSeek",
        "endpoint": "https://api.deepseek.com/v1/",
        "api_key": "",
        "model_id": "deepseek-chat",
        "model_name": "DeepSeek-Chat",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 4. OpenAI
    {
        "provider_id": "openai",
        "provider_name": "OpenAI",
        "endpoint": "https://api.openai.com/v1/",
        "api_key": "",
        "model_id": "gpt-4o",
        "model_name": "GPT-4o",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    {
        "provider_id": "openai",
        "provider_name": "OpenAI",
        "endpoint": "https://api.openai.com/v1/",
        "api_key": "",
        "model_id": "gpt-4o-mini",
        "model_name": "GPT-4o-Mini",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 5. Claude
    {
        "provider_id": "claude",
        "provider_name": "Claude",
        "endpoint": "https://api.anthropic.com/v1/",
        "api_key": "",
        "model_id": "claude-3-5-sonnet-20241022",
        "model_name": "Claude-3.5-Sonnet",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 6. 通义千问
    {
        "provider_id": "tongyi",
        "provider_name": "通义千问",
        "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/",
        "api_key": "",
        "model_id": "qwen-max",
        "model_name": "通义千问-Max",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 7. 豆包
    {
        "provider_id": "doubao",
        "provider_name": "豆包",
        "endpoint": "https://ark.cn-beijing.volces.com/api/v3/",
        "api_key": "",
        "model_id": "doubao-pro-128k",
        "model_name": "豆包-Pro-128K",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 8. Kimi
    {
        "provider_id": "kimi",
        "provider_name": "Kimi",
        "endpoint": "https://api.moonshot.cn/v1/",
        "api_key": "",
        "model_id": "moonshot-v1-8k",
        "model_name": "Kimi-8K",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 9. 智谱清言
    {
        "provider_id": "zhipu",
        "provider_name": "智谱清言",
        "endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "api_key": "",
        "model_id": "glm-4-flash",
        "model_name": "GLM-4-Flash",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 10. ChatGLM
    {
        "provider_id": "chatglm",
        "provider_name": "ChatGLM",
        "endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "api_key": "",
        "model_id": "chatglm_turbo",
        "model_name": "ChatGLM-Turbo",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 11. Google Gemini
    {
        "provider_id": "gemini",
        "provider_name": "Google Gemini",
        "endpoint": "https://generativelanguage.googleapis.com/v1/",
        "api_key": "",
        "model_id": "gemini-1.5-pro",
        "model_name": "Gemini-1.5-Pro",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 12. 文心一言
    {
        "provider_id": "wenxin",
        "provider_name": "文心一言",
        "endpoint": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/",
        "api_key": "",
        "model_id": "ernie-4.0-8k",
        "model_name": "文心一言-4.0",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 13. 腾讯混元
    {
        "provider_id": "hunyuan",
        "provider_name": "腾讯混元",
        "endpoint": "https://hunyuan.tencentcloudapi.com/",
        "api_key": "",
        "model_id": "hunyuan-lite",
        "model_name": "混元-Lite",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 14. 零一万物 Yi
    {
        "provider_id": "yi",
        "provider_name": "零一万物",
        "endpoint": "https://api.lingyiwanwu.com/v1/",
        "api_key": "",
        "model_id": "yi-large",
        "model_name": "Yi-Large",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    },
    # 15. 硅基流动
    {
        "provider_id": "siliconflow",
        "provider_name": "硅基流动",
        "endpoint": "https://api.siliconflow.cn/v1/",
        "api_key": "",
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "model_name": "Qwen2.5-7B-Instruct",
        "type": "chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "status": 0
    }
]

async def init_default_model_configs(db: Session):
    """初始化默认模型配置到数据库"""
    try:
        for config_data in DEFAULT_MODEL_CONFIGS:
            # 检查是否已存在相同的配置
            existing = db.query(ModelConfigModel).filter(
                ModelConfigModel.provider_id == config_data["provider_id"],
                ModelConfigModel.model_id == config_data["model_id"],
                ModelConfigModel.endpoint == config_data["endpoint"]
            ).first()
            
            # 如果不存在，则创建默认配置
            if not existing:
                db_config = ModelConfigModel(
                    id=str(uuid.uuid4()),
                    **config_data
                )
                db.add(db_config)
        
        db.commit()
        print("默认模型配置初始化完成")
    except Exception as e:
        db.rollback()
        print(f"初始化默认模型配置失败: {str(e)}")

@router.get("/providers", response_model=List[ModelProviderResponse])
async def get_providers(db: Session = Depends(get_db)):
    """获取模型提供商列表"""
    try:
        from datetime import datetime
        # 直接返回默认提供商列表，避免数据库关系问题
        current_time = datetime.now()
        return [
            {
                "id": provider["id"],
                "name": provider["name"],
                "api_url": provider["api_url"],
                "created_at": current_time,
                "updated_at": current_time
            }
            for provider in DEFAULT_PROVIDERS
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}")

@router.get("/", response_model=List[ModelConfigResponse])
async def get_model_configs(db: Session = Depends(get_db)):
    """获取模型配置列表"""
    try:
        configs = db.query(ModelConfigModel).all()
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型配置失败: {str(e)}")

@router.post("/", response_model=ModelConfigResponse)
async def create_model_config(
    config: ModelConfigCreate, 
    db: Session = Depends(get_db)
):
    """创建模型配置"""
    try:
        # 检查是否已存在相同的模型配置
        existing = db.query(ModelConfigModel).filter(
            ModelConfigModel.provider_id == config.provider_id,
            ModelConfigModel.model_name == config.model_name,
            ModelConfigModel.endpoint == config.endpoint
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="相同的模型配置已存在")
        
        # 创建新的模型配置
        import uuid
        db_config = ModelConfigModel(
            id=str(uuid.uuid4()),
            user_id=1,  # 默认用户ID
            provider_id=config.provider_id,
            provider_name=config.provider_name,
            endpoint=config.endpoint,
            api_key=config.api_key,
            model_id=config.model_id,
            model_name=config.model_name,
            type=config.type,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            status=config.status
        )
        
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        return db_config
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建模型配置失败: {str(e)}")

@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_model_config(
    config_id: str,
    config: ModelConfigUpdate,
    db: Session = Depends(get_db)
):
    """更新模型配置"""
    try:
        db_config = db.query(ModelConfigModel).filter(ModelConfigModel.id == config_id).first()
        if not db_config:
            raise HTTPException(status_code=404, detail="模型配置不存在")
    
        # 更新字段
        update_data = config.dict(exclude_unset=True)
        for field, value in update_data.items():
            # 将驼峰命名转换为下划线命名
            snake_field = camel_to_snake(field)
            if hasattr(db_config, snake_field):
                setattr(db_config, snake_field, value)
    
        db.commit()
        db.refresh(db_config)
        
        return db_config
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新模型配置失败: {str(e)}")

@router.delete("/{config_id}")
async def delete_model_config(config_id: str, db: Session = Depends(get_db)):
    """删除模型配置"""
    try:
        db_config = db.query(ModelConfigModel).filter(ModelConfigModel.id == config_id).first()
        if not db_config:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        db.delete(db_config)
        db.commit()
        
        return {"message": "模型配置删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除模型配置失败: {str(e)}")

@router.get("/models", response_model=List[ModelResponse])
async def get_models(
    provider_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取指定提供商的模型列表"""
    try:
        if not provider_id:
            return []
        models = db.query(ProviderModel).filter(ProviderModel.provider_id == provider_id).all()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.post("/models/refresh", response_model=List[ModelResponse])
async def refresh_models(
    request: RefreshModelsRequest,
    db: Session = Depends(get_db)
):
    """刷新模型列表"""
    import logging
    from datetime import datetime
    import os
    
    logger = logging.getLogger(__name__)
    
    # 写入详细日志到文件
    log_file = os.path.join(os.path.dirname(__file__), "../../debug_refresh.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n=== 刷新模型请求 {datetime.now()} ===\n")
        f.write(f"endpoint: '{request.endpoint}'\n")
        f.write(f"provider_id: '{request.provider_id}'\n")
        f.write(f"api_key: {'***' if request.api_key else None}\n")
        f.write(f"endpoint类型: {type(request.endpoint)}\n")
        f.write(f"endpoint长度: {len(request.endpoint) if request.endpoint else 0}\n")
    
    logger.info(f"收到刷新模型请求:")
    logger.info(f"  endpoint: {request.endpoint}")
    logger.info(f"  provider_id: {request.provider_id}")
    logger.info(f"  api_key: {'***' if request.api_key else None}")
    
    # 写入进入try块的日志
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"进入try块，准备处理请求...\n")
    
    try:
        # 写入开始处理日志
        log_file = os.path.join(os.path.dirname(__file__), "../../debug_refresh.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"开始调用 fetch_models_from_api...\n")
        
        models = await fetch_models_from_api(
            request.endpoint,
            request.provider_id, 
            request.api_key
        )
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"fetch_models_from_api 返回了 {len(models) if models else 0} 个模型\n")
        
        if models:
            await update_models_in_db(db, request.provider_id, models)
            # 重新从数据库查询模型，确保包含所有字段
            db_models = db.query(ProviderModel).filter(ProviderModel.provider_id == request.provider_id).all()
            return db_models
        
        return []
    except httpx.ConnectError as e:
        raise HTTPException(status_code=503, detail=f"无法连接到模型服务: {str(e)}")
    except httpx.TimeoutException as e:
        raise HTTPException(status_code=504, detail=f"连接超时: {str(e)}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="API Key 无效或权限不足")
        elif e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="模型服务端点不存在")
        else:
            raise HTTPException(status_code=502, detail=f"模型服务返回错误: {e.response.status_code}")
    except Exception as e:
        # 写入异常详情到日志文件
        log_file = os.path.join(os.path.dirname(__file__), "../../debug_refresh.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"refresh_models 异常:\n")
            f.write(f"  异常类型: {type(e).__name__}\n")
            f.write(f"  异常信息: {str(e)}\n")
            import traceback
            f.write(f"  堆栈跟踪: {traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=f"刷新模型列表失败: {str(e)}")

# 辅助函数
def camel_to_snake(name: str) -> str:
    """将驼峰命名转换为下划线命名"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

async def fetch_models_from_api(endpoint: str, provider_id: str, api_key: Optional[str] = None):
    """从API获取模型列表"""
    import logging
    import os
    logger = logging.getLogger(__name__)
    
    # 写入函数开始日志
    log_file = os.path.join(os.path.dirname(__file__), "../../debug_refresh.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"fetch_models_from_api 函数开始执行\n")
        f.write(f"  参数: endpoint='{endpoint}', provider_id='{provider_id}'\n")
    
    logger.info(f"正在从 {provider_id} 获取模型列表: {endpoint}")
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # 增加超时时间，设置重试机制
    timeout = httpx.Timeout(30.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if provider_id.lower() == "ollama":
                # Ollama API
                models_endpoint = f"{endpoint.rstrip('/')}/tags"
                logger.info(f"请求 Ollama 端点: {models_endpoint}")
                response = await client.get(models_endpoint)
            else:
                # OpenAI compatible API (包括vLLM)
                if provider_id.lower() == "vllm":
                    # vLLM使用 /v1/models 端点，智能处理是否已包含v1
                    endpoint_clean = endpoint.rstrip('/')
                    if endpoint_clean.endswith('/v1'):
                        models_endpoint = f"{endpoint_clean}/models"
                    else:
                        models_endpoint = f"{endpoint_clean}/v1/models"
                else:
                    # 其他OpenAI兼容API使用 /models 端点
                    models_endpoint = f"{endpoint.rstrip('/')}/models"
                
                logger.info(f"请求 OpenAI 兼容端点: {models_endpoint}")
                logger.info(f"原始endpoint: '{endpoint}', 清理后: '{endpoint.rstrip('/')}', 最终URL: '{models_endpoint}'")
                
                # 写入URL构建详情到日志文件
                log_file = os.path.join(os.path.dirname(__file__), "../../debug_refresh.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"URL构建详情:\n")
                    f.write(f"  原始endpoint: '{endpoint}'\n")
                    f.write(f"  清理后endpoint: '{endpoint.rstrip('/')}'\n")
                    f.write(f"  是否以/v1结尾: {endpoint.rstrip('/').endswith('/v1')}\n")
                    f.write(f"  最终URL: '{models_endpoint}'\n")
                
                # vLLM通常不需要API key，先尝试不带headers的请求
                if provider_id.lower() == "vllm":
                    logger.info(f"发送vLLM请求到: {models_endpoint}")
                    response = await client.get(models_endpoint)
                else:
                    logger.info(f"发送OpenAI兼容请求到: {models_endpoint}")
                    response = await client.get(models_endpoint, headers=headers)
            
            logger.info(f"HTTP 响应状态: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"响应数据: {data}")
            
            models = []
            if provider_id.lower() == "ollama":
                # Ollama格式
                for model in data.get("models", []):
                    # 生成安全的ID，替换特殊字符
                    safe_model_name = model['name'].replace(':', '_').replace('/', '_').replace('.', '_')
                    
                    # 处理modified_at字段
                    modified_at = model.get("modified_at")
                    if modified_at and isinstance(modified_at, str):
                        from datetime import datetime
                        try:
                            # 尝试解析ISO格式的时间字符串
                            modified_at = datetime.fromisoformat(modified_at.replace('Z', '+00:00'))
                        except:
                            modified_at = None
                    elif modified_at and isinstance(modified_at, (int, float)):
                        from datetime import datetime
                        modified_at = datetime.fromtimestamp(modified_at)
                    
                    models.append({
                        "id": f"{provider_id}_{safe_model_name}",
                        "provider_id": provider_id,
                        "model_id": model["name"],
                        "model_name": model["name"],
                        "size": model.get("size", 0),
                        "created_at": modified_at
                    })
            else:
                # OpenAI格式（包括vLLM）
                for model in data.get("data", []):
                    # 生成安全的ID，替换特殊字符
                    safe_model_id = model['id'].replace(':', '_').replace('/', '_').replace('.', '_').replace('-', '_')
                    
                    # 处理created_at字段，转换Unix时间戳为datetime对象
                    created_at = model.get("created")
                    if created_at and isinstance(created_at, (int, float)):
                        from datetime import datetime
                        created_at = datetime.fromtimestamp(created_at)
                    
                    models.append({
                        "id": f"{provider_id}_{safe_model_id}",
                        "provider_id": provider_id,
                        "model_id": model["id"],
                        "model_name": model["id"],
                        "created_at": created_at
                    })
            
            logger.info(f"成功解析 {len(models)} 个模型")
            return models
            
        except httpx.ConnectError as e:
            logger.error(f"连接错误: {str(e)}")
            # 写入错误详情到日志文件
            log_file = os.path.join(os.path.dirname(__file__), "../../debug_refresh.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"连接错误详情:\n")
                f.write(f"  错误类型: {type(e).__name__}\n")
                f.write(f"  错误信息: {str(e)}\n")
                f.write(f"  尝试连接的URL: {models_endpoint}\n")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"超时错误: {str(e)}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            raise

async def update_models_in_db(db: Session, provider_id: str, models: List[dict]):
    """更新数据库中的模型列表"""
    # 删除旧的模型数据
    db.query(ProviderModel).filter(ProviderModel.provider_id == provider_id).delete()
    
    # 添加新的模型数据
    for model_data in models:
        model = ProviderModel(
            id=model_data["id"],
            provider_id=model_data["provider_id"],
            model_id=model_data["model_id"], 
            model_name=model_data["model_name"],
            size=model_data.get("size"),
            description=model_data.get("description"),
            is_vision=model_data.get("is_vision", False),
            status=model_data.get("status", 1),
            created_at=model_data.get("created_at")
        )
        db.add(model)
    
    db.commit() 