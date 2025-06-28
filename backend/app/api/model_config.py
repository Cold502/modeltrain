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
    models = await fetch_models_from_api(
        request.endpoint,
        request.provider_id, 
        request.api_key
    )
    
    if models:
        await update_models_in_db(db, request.provider_id, models)
    
    return models

# 辅助函数
def camel_to_snake(name: str) -> str:
    """将驼峰命名转换为下划线命名"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

async def fetch_models_from_api(endpoint: str, provider_id: str, api_key: Optional[str] = None):
    """从API获取模型列表"""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        if provider_id.lower() == "ollama":
            # Ollama API
            response = await client.get(f"{endpoint}/tags")
        else:
            # OpenAI compatible API (包括vLLM)
            models_endpoint = f"{endpoint.rstrip('/')}/models"
            # vLLM通常不需要API key，先尝试不带headers的请求
            if provider_id.lower() == "vllm":
                response = await client.get(models_endpoint)
            else:
                response = await client.get(models_endpoint, headers=headers)
        
        response.raise_for_status()
        data = response.json()
        
        models = []
        if provider_id.lower() == "ollama":
            # Ollama格式
            for model in data.get("models", []):
                # 生成安全的ID，替换特殊字符
                safe_model_name = model['name'].replace(':', '_').replace('/', '_').replace('.', '_')
                models.append({
                    "id": f"{provider_id}_{safe_model_name}",
                    "provider_id": provider_id,
                    "model_id": model["name"],
                    "model_name": model["name"],
                    "size": model.get("size", 0),
                    "created_at": model.get("modified_at")
                })
        else:
            # OpenAI格式（包括vLLM）
            for model in data.get("data", []):
                # 生成安全的ID，替换特殊字符
                safe_model_id = model['id'].replace(':', '_').replace('/', '_').replace('.', '_').replace('-', '_')
                models.append({
                    "id": f"{provider_id}_{safe_model_id}",
                    "provider_id": provider_id,
                    "model_id": model["id"],
                    "model_name": model["id"],
                    "created_at": model.get("created")
                })
        
        return models

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
            created_at=model_data.get("created_at")
        )
        db.add(model)
    
    db.commit() 