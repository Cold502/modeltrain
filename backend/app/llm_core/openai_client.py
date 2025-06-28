import json
from typing import Dict, List, Any
from .base_client import BaseClient
import httpx

class OpenAIClient(BaseClient):
    """OpenAI兼容客户端"""
    
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
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream('POST', url, json=payload, headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}' if self.api_key else ''
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
        current_thinking = ""
        current_content = ""
        
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
                        break
                    
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
                                current_thinking += reasoning
                            
                            # 处理正常内容
                            if content:
                                if is_thinking:
                                    yield '</think>'
                                    is_thinking = False
                                yield content
                                current_content += content
                                
                    except json.JSONDecodeError:
                        continue 