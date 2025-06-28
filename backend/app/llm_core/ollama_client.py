import json
from typing import Dict, List, Any
from .base_client import BaseClient
import httpx

class OllamaClient(BaseClient):
    """Ollama客户端"""
    
    async def chat(self, messages: List[Dict], options: Dict = None) -> Dict:
        """普通聊天"""
        if options is None:
            options = {}
            
        payload = {
            'model': self.model,
            'messages': self._convert_messages(messages),
            'stream': False,
            'options': {
                'temperature': options.get('temperature', self.model_config['temperature']),
                'top_p': options.get('top_p', self.model_config['top_p']),
                'num_predict': options.get('max_tokens', self.model_config['max_tokens'])
            }
        }
        
        # 确保endpoint格式正确
        base_url = self.endpoint.rstrip('/')
        if base_url.endswith('/api'):
            base_url = base_url[:-4]
        
        url = f"{base_url}/api/chat"
        result = await self._make_request_ollama(url, payload)
        
        return {
            'text': result['message']['content'],
            'response': result
        }
    
    async def chat_stream(self, messages: List[Dict], options: Dict = None):
        """流式聊天"""
        if options is None:
            options = {}
            
        payload = {
            'model': self.model,
            'messages': self._convert_messages(messages),
            'stream': True,
            'options': {
                'temperature': options.get('temperature', self.model_config['temperature']),
                'top_p': options.get('top_p', self.model_config['top_p']),
                'num_predict': options.get('max_tokens', self.model_config['max_tokens'])
            }
        }
        
        # 确保endpoint格式正确
        base_url = self.endpoint.rstrip('/')
        if base_url.endswith('/api'):
            base_url = base_url[:-4]
        
        url = f"{base_url}/api/chat"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream('POST', url, json=payload, headers={
                'Content-Type': 'application/json'
            }) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"API请求失败: {response.status_code} {error_text}")
                
                # 创建流式处理器
                return self._create_stream_processor(response)
    
    async def _create_stream_processor(self, response):
        """创建流式处理器"""
        buffer = ""
        is_thinking = False
        
        async for chunk in response.aiter_text():
            buffer += chunk
            
            # 处理数据行
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                
                if line:
                    try:
                        data = json.loads(line)
                        message = data.get('message', {})
                        content = message.get('content', '')
                        thinking = message.get('thinking', '')
                        done = data.get('done', False)
                        
                        # 处理推理内容
                        if thinking:
                            if not is_thinking:
                                yield '<think>'
                                is_thinking = True
                            yield thinking
                        
                        # 处理正常内容
                        if content:
                            if is_thinking:
                                yield '</think>'
                                is_thinking = False
                            yield content
                        
                        if done:
                            if is_thinking:
                                yield '</think>'
                            break
                            
                    except json.JSONDecodeError:
                        continue
    
    async def _make_request_ollama(self, url: str, payload: Dict):
        """发起Ollama专用请求"""
        headers = {'Content-Type': 'application/json'}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"API请求失败: {response.status_code} {response.text}")
            return response.json()
    
    async def get_models(self):
        """获取可用模型列表"""
        base_url = self.endpoint.rstrip('/')
        if base_url.endswith('/api'):
            base_url = base_url[:-4]
        
        url = f"{base_url}/api/tags"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            
            data = response.json()
            if 'models' in data:
                return [
                    {
                        'name': model['name'],
                        'modified_at': model.get('modified_at'),
                        'size': model.get('size')
                    }
                    for model in data['models']
                ]
            return [] 