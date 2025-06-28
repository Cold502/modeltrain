from typing import Dict, List, Any, Optional
from .openai_client import OpenAIClient
from .ollama_client import OllamaClient

# 默认模型设置
DEFAULT_MODEL_SETTINGS = {
    'temperature': 0.7,
    'max_tokens': 8192,
    'top_p': 0.9,
    'top_k': 0.0
}

# 模型提供商配置
MODEL_PROVIDERS = [
    {
        'id': 'ollama',
        'name': 'Ollama',
        'default_endpoint': 'http://127.0.0.1:11434/api',
        'default_models': []
    },
    {
        'id': 'vllm',
        'name': 'VLLM',
        'default_endpoint': 'http://127.0.0.1:8000/v1/',
        'default_models': []
    },
    {
        'id': 'openai',
        'name': 'OpenAI',
        'default_endpoint': 'https://api.openai.com/v1/',
        'default_models': ['gpt-4o', 'gpt-4o-mini', 'o1-mini']
    },
    {
        'id': 'siliconcloud',
        'name': '硅基流动',
        'default_endpoint': 'https://api.siliconflow.cn/v1/',
        'default_models': [
            'deepseek-ai/DeepSeek-R1',
            'deepseek-ai/DeepSeek-V3',
            'Qwen2.5-7B-Instruct',
            'meta-llama/Llama-3.3-70B-Instruct'
        ]
    },
    {
        'id': 'deepseek',
        'name': 'DeepSeek',
        'default_endpoint': 'https://api.deepseek.com/v1/',
        'default_models': ['deepseek-chat', 'deepseek-reasoner']
    },
    {
        'id': '302ai',
        'name': '302.AI',
        'default_endpoint': 'https://api.302.ai/v1/',
        'default_models': ['Doubao-pro-128k', 'deepseek-r1', 'kimi-latest', 'qwen-max']
    },
    {
        'id': 'zhipu',
        'name': '智谱AI',
        'default_endpoint': 'https://open.bigmodel.cn/api/paas/v4/',
        'default_models': ['glm-4-flash', 'glm-4-flashx', 'glm-4-plus', 'glm-4-long']
    }
]

class LLMClient:
    """统一LLM客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM客户端
        
        Args:
            config: 配置字典，包含以下字段：
                - provider_id: 提供商ID
                - endpoint: API端点
                - api_key: API密钥
                - model_name: 模型名称
                - temperature: 温度参数
                - max_tokens: 最大token数
                - top_p: top_p参数
                - top_k: top_k参数
        """
        self.config = {
            'provider': config.get('provider_id', 'openai'),
            'endpoint': self._handle_endpoint(config.get('provider_id'), config.get('endpoint', '')),
            'api_key': config.get('api_key', ''),
            'model_name': config.get('model_name', ''),
            'temperature': config.get('temperature', DEFAULT_MODEL_SETTINGS['temperature']),
            'max_tokens': config.get('max_tokens', DEFAULT_MODEL_SETTINGS['max_tokens']),
            'top_p': config.get('top_p', DEFAULT_MODEL_SETTINGS['top_p']),
            'top_k': config.get('top_k', DEFAULT_MODEL_SETTINGS['top_k'])
        }
        
        self.client = self._create_client(self.config['provider'], self.config)
    
    def _handle_endpoint(self, provider: str, endpoint: str) -> str:
        """处理端点URL兼容性"""
        if not endpoint:
            return ''
            
        if provider and provider.lower() == 'ollama':
            if endpoint.endswith('v1/') or endpoint.endswith('v1'):
                return endpoint.replace('v1', 'api')
        
        if endpoint.endswith('/chat/completions'):
            return endpoint.replace('/chat/completions', '')
            
        return endpoint
    
    def _create_client(self, provider: str, config: Dict[str, Any]):
        """创建具体的客户端实例"""
        provider_lower = provider.lower()
        
        if provider_lower == 'ollama':
            return OllamaClient(config)
        else:
            # vLLM和其他提供商使用OpenAI兼容客户端
            # vLLM提供OpenAI兼容的API接口，可以直接使用OpenAI客户端
            return OpenAIClient(config)
    
    async def chat(self, messages: List[Dict], options: Optional[Dict] = None) -> Dict:
        """普通聊天"""
        if options is None:
            options = {}
        
        # 合并配置
        merged_options = {**self.config, **options}
        
        return await self.client.chat(messages, merged_options)
    
    async def chat_stream(self, messages: List[Dict], options: Optional[Dict] = None):
        """流式聊天"""
        if options is None:
            options = {}
        
        # 合并配置
        merged_options = {**self.config, **options}
        
        return await self.client.chat_stream(messages, merged_options)
    
    async def get_response(self, messages: List[Dict], options: Optional[Dict] = None) -> str:
        """获取简单响应文本"""
        result = await self.chat(messages, options)
        return result.get('text', '')
    
    async def get_response_with_cot(self, messages: List[Dict], options: Optional[Dict] = None) -> Dict:
        """获取带推理链的响应"""
        if options is None:
            options = {}
        
        # 启用推理模式
        options['extra_body'] = {'enable_thinking': True}
        
        result = await self.chat(messages, options)
        response_text = result.get('text', '')
        
        # 解析推理链和答案
        thinking = ''
        answer = response_text
        
        if '<think>' in response_text and '</think>' in response_text:
            parts = response_text.split('<think>')
            if len(parts) >= 2:
                think_part = parts[1].split('</think>')
                if len(think_part) >= 2:
                    thinking = think_part[0].strip()
                    answer = think_part[1].strip()
        
        return {
            'answer': answer,
            'cot': thinking
        }

def get_model_providers() -> List[Dict]:
    """获取模型提供商列表"""
    return MODEL_PROVIDERS

def get_default_model_settings() -> Dict:
    """获取默认模型设置"""
    return DEFAULT_MODEL_SETTINGS.copy() 