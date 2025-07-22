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
        'default_models': [],
        'requires_api_key': False  # Ollama本地服务不需要API key
    },
    {
        'id': 'vllm',
        'name': 'VLLM',
        'default_endpoint': 'http://127.0.0.1:8000/v1/',
        'default_models': [],
        'requires_api_key': False  # vLLM本地服务不需要API key
    },
    {
        'id': 'openai',
        'name': 'OpenAI',
        'default_endpoint': 'https://api.openai.com/v1/',
        'default_models': ['gpt-4o', 'gpt-4o-mini', 'o1-mini'],
        'requires_api_key': True
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
        ],
        'requires_api_key': True
    },
    {
        'id': 'deepseek',
        'name': 'DeepSeek',
        'default_endpoint': 'https://api.deepseek.com/v1/',
        'default_models': ['deepseek-chat', 'deepseek-reasoner'],
        'requires_api_key': True
    },
    {
        'id': '302ai',
        'name': '302.AI',
        'default_endpoint': 'https://api.302.ai/v1/',
        'default_models': ['Doubao-pro-128k', 'deepseek-r1', 'kimi-latest', 'qwen-max'],
        'requires_api_key': True
    },
    {
        'id': 'zhipu',
        'name': '智谱AI',
        'default_endpoint': 'https://open.bigmodel.cn/api/paas/v4/',
        'default_models': ['glm-4-flash', 'glm-4-flashx', 'glm-4-plus', 'glm-4-long'],
        'requires_api_key': True
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
        provider_id = config.get('provider_id', 'openai')
        
        # 检查该提供商是否需要API key
        provider_info = self._get_provider_info(provider_id)
        requires_api_key = provider_info.get('requires_api_key', True) if provider_info else True
        
        # 对于不需要API key的提供商，忽略用户输入的API key
        api_key = config.get('api_key', '') if requires_api_key else ''
        
        self.config = {
            'provider': provider_id,
            'endpoint': self._handle_endpoint(provider_id, config.get('endpoint', '')),
            'api_key': api_key,
            'model_name': config.get('model_name', ''),
            'temperature': config.get('temperature', DEFAULT_MODEL_SETTINGS['temperature']),
            'max_tokens': config.get('max_tokens', DEFAULT_MODEL_SETTINGS['max_tokens']),
            'top_p': config.get('top_p', DEFAULT_MODEL_SETTINGS['top_p']),
            'top_k': config.get('top_k', DEFAULT_MODEL_SETTINGS['top_k']),
            'requires_api_key': requires_api_key
        }
        
        self.client = self._create_client(self.config['provider'], self.config)
    
    def _get_provider_info(self, provider_id: str) -> Optional[Dict]:
        """获取提供商信息"""
        for provider in MODEL_PROVIDERS:
            if provider['id'] == provider_id:
                return provider
        return None
    
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
    
    async def get_response_with_cot(self, messages: List[Dict], options: Optional[Dict] = None) -> Dict[str, str]:
        """获取带思维链的响应"""
        if options is None:
            options = {}
        
        # 对于支持推理的模型（如DeepSeek R1），添加推理参数
        provider_lower = self.config.get('provider', '').lower()
        if provider_lower in ['deepseek', 'openai']:
            options['extra_body'] = {
                'reasoning': True,
                'send_reasoning': True
            }
        
        try:
            result = await self.chat(messages, options)
            response_text = result.get('text', '')
            
            # 解析思维链内容
            cot = ""
            answer = response_text
            
            if '<think>' in response_text and '</think>' in response_text:
                import re
                think_match = re.search(r'<think>(.*?)</think>', response_text, re.DOTALL)
                if think_match:
                    cot = think_match.group(1).strip()
                    answer = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
            
            return {
                'answer': answer,
                'cot': cot
            }
        except Exception as e:
            # 如果调用失败，返回错误信息
            return {
                'answer': f'抱歉，模型调用失败: {str(e)}',
                'cot': ''
            }

def get_model_providers() -> List[Dict]:
    """获取模型提供商列表"""
    return MODEL_PROVIDERS

def get_default_model_settings() -> Dict:
    """获取默认模型设置"""
    return DEFAULT_MODEL_SETTINGS.copy() 

def provider_requires_api_key(provider_id: str) -> bool:
    """检查指定提供商是否需要API key"""
    for provider in MODEL_PROVIDERS:
        if provider['id'] == provider_id:
            return provider.get('requires_api_key', True)
    return True  # 默认需要API key 