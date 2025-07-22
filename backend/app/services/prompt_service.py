"""
系统提示词服务
处理提示词格式转换、预定义模板等功能
"""

from typing import Dict, List, Any
import json
import re


class PromptService:
    """系统提示词服务类"""
    
    # 预定义系统提示词模板
    PREDEFINED_PROMPTS = {
        "general": {
            "name": "通用助手",
            "description": "一个有用、无害、诚实的AI助手",
            "content": "你是一个有用、无害、诚实的AI助手。请根据用户的问题提供准确、有用的回答。",
            "format_type": "openai",
            "category": "general"
        },
        "coding": {
            "name": "编程助手",
            "description": "专业的编程和技术问题助手",
            "content": "你是一个专业的编程助手。你擅长多种编程语言，包括Python、JavaScript、Java、C++等。请为用户提供准确的代码建议、调试帮助和技术解决方案。在回答时，请提供清晰的代码示例和详细的解释。",
            "format_type": "openai",
            "category": "coding"
        },
        "translation": {
            "name": "翻译助手",
            "description": "多语言翻译专家",
            "content": "你是一个专业的翻译助手。你能够准确地在中文、英文、日文、韩文、法文、德文、西班牙文等多种语言之间进行翻译。请保持翻译的准确性和自然性，同时考虑文化背景和语境。",
            "format_type": "openai",
            "category": "translation"
        },
        "creative": {
            "name": "创意写作助手",
            "description": "创意写作和文案创作专家",
            "content": "你是一个富有创意的写作助手。你擅长创作故事、诗歌、广告文案、营销内容等各种文体。请发挥你的想象力和创造力，为用户提供原创、有趣、引人入胜的内容。",
            "format_type": "openai",
            "category": "creative"
        },
        "academic": {
            "name": "学术研究助手",
            "description": "学术论文和研究支持专家",
            "content": "你是一个学术研究助手。你熟悉各种学科的研究方法、论文写作规范和学术标准。请为用户提供专业的学术建议、论文结构指导、文献综述帮助等服务。请确保信息的准确性和学术严谨性。",
            "format_type": "openai",
            "category": "academic"
        },
        "business": {
            "name": "商业顾问",
            "description": "商业策略和管理咨询专家",
            "content": "你是一个经验丰富的商业顾问。你擅长商业策略分析、市场研究、财务规划、团队管理等领域。请为用户提供实用的商业建议和解决方案，帮助他们做出明智的商业决策。",
            "format_type": "openai",
            "category": "business"
        }
    }
    
    @classmethod
    def convert_format(cls, content: str, source_format: str, target_format: str) -> Dict[str, Any]:
        """
        转换提示词格式
        
        Args:
            content: 提示词内容
            source_format: 源格式 (openai, ollama, custom)
            target_format: 目标格式 (openai, ollama, custom)
            
        Returns:
            Dict containing converted content and format info
        """
        if source_format == target_format:
            return {
                "converted_content": content,
                "format_info": {
                    "source_format": source_format,
                    "target_format": target_format,
                    "changes": "无变化"
                }
            }
        
        converted_content = content
        changes = []
        
        if target_format == "openai":
            converted_content, format_changes = cls._convert_to_openai(content, source_format)
            changes.extend(format_changes)
        elif target_format == "ollama":
            converted_content, format_changes = cls._convert_to_ollama(content, source_format)
            changes.extend(format_changes)
        elif target_format == "custom":
            converted_content, format_changes = cls._convert_to_custom(content, source_format)
            changes.extend(format_changes)
        
        return {
            "converted_content": converted_content,
            "format_info": {
                "source_format": source_format,
                "target_format": target_format,
                "changes": changes
            }
        }
    
    @classmethod
    def _convert_to_openai(cls, content: str, source_format: str) -> tuple[str, List[str]]:
        """转换为OpenAI格式"""
        changes = []
        
        if source_format == "ollama":
            # Ollama格式通常使用特殊标记，需要转换为标准文本
            content = re.sub(r'\{\{\s*\.System\s*\}\}', '', content)
            content = re.sub(r'\{\{\s*\.Content\s*\}\}', '', content)
            changes.append("移除Ollama模板标记")
        
        # OpenAI格式规范化
        content = content.strip()
        if not content.endswith('.') and not content.endswith('。'):
            content += '。'
            changes.append("添加句号结尾")
        
        return content, changes
    
    @classmethod
    def _convert_to_ollama(cls, content: str, source_format: str) -> tuple[str, List[str]]:
        """转换为Ollama格式"""
        changes = []
        
        if source_format == "openai":
            # 为Ollama格式添加模板结构
            ollama_content = f"""# System Message
{content}

# Template Structure
This system message will be applied to all conversations."""
            changes.append("添加Ollama模板结构")
            return ollama_content, changes
        
        return content, changes
    
    @classmethod
    def _convert_to_custom(cls, content: str, source_format: str) -> tuple[str, List[str]]:
        """转换为自定义格式"""
        changes = []
        
        # 自定义格式保持原样，但添加元数据注释
        custom_content = f"""<!-- Custom Format System Prompt -->
<!-- Source Format: {source_format} -->
{content}
<!-- End Custom Format -->"""
        
        changes.append("添加自定义格式元数据")
        return custom_content, changes
    
    @classmethod
    def get_predefined_prompts(cls) -> List[Dict[str, Any]]:
        """获取所有预定义提示词"""
        prompts = []
        for key, prompt in cls.PREDEFINED_PROMPTS.items():
            prompts.append({
                "key": key,
                **prompt
            })
        return prompts
    
    @classmethod
    def get_prompt_by_key(cls, key: str) -> Dict[str, Any]:
        """根据key获取预定义提示词"""
        return cls.PREDEFINED_PROMPTS.get(key)
    
    @classmethod
    def validate_prompt_format(cls, content: str, format_type: str) -> Dict[str, Any]:
        """验证提示词格式"""
        errors = []
        warnings = []
        
        if not content.strip():
            errors.append("提示词内容不能为空")
        
        if len(content) > 10000:
            warnings.append("提示词过长，可能影响模型性能")
        
        if format_type == "openai":
            if "{{" in content or "}}" in content:
                warnings.append("OpenAI格式中检测到模板语法，可能需要转换")
        
        elif format_type == "ollama":
            if not any(marker in content for marker in ["{{", "TEMPLATE", "SYSTEM"]):
                warnings.append("Ollama格式建议包含模板标记")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @classmethod
    def generate_example_usage(cls, content: str, format_type: str) -> Dict[str, Any]:
        """生成使用示例"""
        examples = {}
        
        if format_type == "openai":
            examples["openai_chat"] = {
                "messages": [
                    {"role": "system", "content": content},
                    {"role": "user", "content": "Hello!"},
                    {"role": "assistant", "content": "Hello! How can I help you today?"}
                ]
            }
        
        elif format_type == "ollama":
            examples["ollama_modelfile"] = f"""FROM llama3
SYSTEM \"\"\"{content}\"\"\"
PARAMETER temperature 0.7
PARAMETER top_p 0.9"""
        
        content_short = content[:100] + "..." if len(content) > 100 else content
        examples["curl_example"] = (
            "curl -X POST http://localhost:11434/api/chat \\\n"
            "  -H \"Content-Type: application/json\" \\\n"
            "  -d '{\n"
            "    \"model\": \"your-model\",\n"
            "    \"messages\": [\n"
            f"      {{\"role\": \"system\", \"content\": \"{content_short}\"}},\n"
            "      {\"role\": \"user\", \"content\": \"Your question here\"}\n"
            "    ]\n"
            "  }'"
        )
        
        return examples 