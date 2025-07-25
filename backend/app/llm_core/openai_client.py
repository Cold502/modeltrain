import json
from typing import Dict, List, Any
from .base_client import BaseClient
import httpx

class OpenAIClient(BaseClient):
    """OpenAI兼容客户端"""
    
    def __init__(self, config):
        super().__init__(config)
        # 检查是否需要API key
        self.requires_api_key = config.get('requires_api_key', True)
    
    async def chat(self, messages: List[Dict], options: Dict = None) -> Dict:
        """普通聊天"""
        if options is None:
            options = {}
            
        payload = {
            'model': self.model,
            'messages': self._convert_messages(messages),
            'temperature': options.get('temperature', self.model_config['temperature']),
            'max_tokens': options.get('max_tokens', self.model_config['max_tokens']),
            'top_p': options.get('top_p', self.model_config['top_p']),
            'stream': False
        }
        
        # 添加思维链参数（如果支持）
        if 'extra_body' in options:
            payload.update(options['extra_body'])
        
        url = f"{self.endpoint.rstrip('/')}/chat/completions"
        result = await self._make_request(url, payload)
        
        return {
            'text': result['choices'][0]['message']['content'],
            'response': result
        }
    
    async def chat_stream(self, messages: List[Dict], options: Dict = None):
        """流式聊天"""
        if options is None:
            options = {}
            
        payload = {
            'model': self.model,
            'messages': self._convert_messages(messages),
            'temperature': options.get('temperature', self.model_config['temperature']),
            'max_tokens': options.get('max_tokens', self.model_config['max_tokens']),
            'top_p': options.get('top_p', self.model_config['top_p']),
            'stream': True
        }
        
        # 添加推理参数
        payload['send_reasoning'] = True
        payload['reasoning'] = True
        
        url = f"{self.endpoint.rstrip('/')}/chat/completions"
        
        # 创建流式生成器
        async def stream_generator():
            try:
                headers = {'Content-Type': 'application/json'}
                if self.requires_api_key and self.api_key and self.api_key.strip():
                    headers['Authorization'] = f'Bearer {self.api_key}'
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream('POST', url, json=payload, headers=headers) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            raise Exception(f"API请求失败: {response.status_code} {error_text}")
                        
                        buffer = ""
                        is_thinking = False
                        
                        async for chunk in response.aiter_text():
                            buffer += chunk
                            
                            # 处理数据行
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = line.strip()
                                
                                if line and line.startswith('data: '):
                                    data_str = line[6:]
                                    if data_str == '[DONE]':
                                        if is_thinking:
                                            yield '</think>'
                                        return
                                    
                                    try:
                                        data = json.loads(data_str)
                                        if 'choices' in data and len(data['choices']) > 0:
                                            delta = data['choices'][0].get('delta', {})
                                            content = delta.get('content', '')
                                            reasoning = delta.get('reasoning', '')
                                            
                                            # 处理推理内容
                                            if reasoning:
                                                if not is_thinking:
                                                    yield '<think>'
                                                    is_thinking = True
                                                yield reasoning
                                            
                                            # 处理正常内容
                                            if content:
                                                if is_thinking:
                                                    yield '</think>'
                                                    is_thinking = False
                                                yield content
                                                
                                    except json.JSONDecodeError:
                                        continue 
                                            
            except Exception as e:
                # 如果流式请求失败，回退到普通请求并模拟流式输出
                try:
                    print(f"流式请求失败，回退到普通请求: {str(e)}")
                    payload['stream'] = False
                    fallback_headers = {'Content-Type': 'application/json'}
                    if self.requires_api_key and self.api_key and self.api_key.strip():
                        fallback_headers['Authorization'] = f'Bearer {self.api_key}'
                        
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(url, json=payload, headers=fallback_headers)
                        
                        if response.status_code != 200:
                            raise Exception(f"普通API请求也失败: {response.status_code} {response.text}")
                        
                        result = response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # 模拟流式输出，逐字符输出
                        import asyncio
                        for char in content:
                            yield char
                            await asyncio.sleep(0.02)  # 模拟延迟
                            
                except Exception as fallback_error:
                    yield f"[ERROR] 所有请求都失败: {str(fallback_error)}"
        
        return stream_generator()
    
    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """转换消息格式为OpenAI格式"""
        converted = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            converted.append({
                'role': role,
                'content': content
            })
        return converted
    
    async def _make_request(self, url: str, payload: Dict) -> Dict:
        """发送HTTP请求"""
        headers = {'Content-Type': 'application/json'}
        
        # 只有当需要API key且API key存在时才添加Authorization头
        if self.requires_api_key and self.api_key and self.api_key.strip():
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"API请求失败: {response.status_code} {response.text}")
            
            return response.json() 