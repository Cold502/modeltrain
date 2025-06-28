import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import httpx

class BaseClient(ABC):
    """LLM客户端基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.endpoint = config.get('endpoint', '')
        self.api_key = config.get('api_key', '')
        self.model = config.get('model_name', '')
        self.model_config = {
            'temperature': config.get('temperature', 0.7),
            'top_p': config.get('top_p', 0.9),
            'max_tokens': config.get('max_tokens', 8192)
        }

    @abstractmethod
    async def chat(self, messages: List[Dict], options: Dict = None) -> Dict:
        """普通聊天"""
        pass

    @abstractmethod
    async def chat_stream(self, messages: List[Dict], options: Dict = None):
        """流式聊天"""
        pass

    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """转换消息格式"""
        converted = []
        for msg in messages:
            if isinstance(msg.get('content'), str):
                converted.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            elif isinstance(msg.get('content'), list):
                # 处理多模态消息
                converted.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            else:
                converted.append(msg)
        return converted

    async def _make_request(self, url: str, payload: Dict, stream: bool = False):
        """发起HTTP请求"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                async with client.stream('POST', url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise Exception(f"API请求失败: {response.status_code} {error_text}")
                    return response
            else:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    raise Exception(f"API请求失败: {response.status_code} {response.text}")
                return response.json() 