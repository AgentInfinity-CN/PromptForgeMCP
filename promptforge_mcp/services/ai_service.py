#!/usr/bin/env python3
"""
AI服务管理模块
支持OpenAI和Anthropic API调用
"""

import httpx
from typing import Dict, List
from promptforge_mcp.config.config import Config
from promptforge_mcp.models.models import PromptMetrics


class AIServiceManager:
    """AI服务管理器 - 支持OpenAI和Anthropic"""
    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def call_ai(self, messages: List[Dict], model: str = "", 
                     temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """调用AI服务 - 根据模型自动选择提供商"""
        
        # 验证输入参数
        self._validate_messages(messages)
        
        if temperature < 0 or temperature > 2:
            raise ValueError("temperature参数必须在0-2之间")
        
        if max_tokens < 0:
            raise ValueError("max_tokens参数不能为负数")
        
        # 如果没有指定模型，使用默认模型
        if not model:
            model = self.config.default_execution_model
        
        # 根据模型名称判断使用哪个提供商
        provider = self._get_provider_from_model(model)
        
        if provider == "anthropic":
            return await self._call_anthropic(messages, model, temperature, max_tokens)
        elif provider == "openai":
            return await self._call_openai(messages, model, temperature, max_tokens)
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")
    
    async def _call_openai(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> str:
        """调用OpenAI API"""
        if not self.config.openai_api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        # 默认模型
        if not model:
            model = "gpt-4"
        
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens > 0:
            request_data["max_tokens"] = max_tokens
        
        endpoint = f"{self.config.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.openai_api_key}"
        }
        
        try:
            response = await self.client.post(endpoint, json=request_data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if not result.get("choices"):
                raise ValueError("OpenAI API返回空响应")
            
            return result["choices"][0]["message"]["content"]
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            raise ValueError(f"OpenAI API请求失败 (状态码: {e.response.status_code}): {error_text}")
        except Exception as e:
            raise ValueError(f"OpenAI API调用错误: {str(e)}")
    
    async def _call_anthropic(self, messages: List[Dict], model: str, temperature: float, max_tokens: int) -> str:
        """调用Anthropic API"""
        if not self.config.anthropic_api_key:
            raise ValueError("Anthropic API密钥未配置")
        
        # 默认模型
        if not model:
            model = "claude-3-7-sonnet-20250219"
        
        # Anthropic temperature范围是0-1，OpenAI是0-2，需要转换
        anthropic_temperature = min(max(temperature / 2.0 if temperature > 1.0 else temperature, 0), 1)
        
        # 转换消息格式 - Anthropic需要分离system消息
        anthropic_messages = []
        system_message = ""
        
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                anthropic_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content", "")
                })
        
        request_data = {
            "model": model,
            "max_tokens": max_tokens if max_tokens > 0 else 1000,  # Anthropic要求max_tokens
            "temperature": anthropic_temperature,
            "messages": anthropic_messages
        }
        
        if system_message:
            request_data["system"] = system_message
        
        endpoint = f"{self.config.anthropic_base_url.rstrip('/')}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        try:
            response = await self.client.post(endpoint, json=request_data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if not result.get("content"):
                raise ValueError("Anthropic API返回空响应")
            
            return result["content"][0]["text"]
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            raise ValueError(f"Anthropic API请求失败 (状态码: {e.response.status_code}): {error_text}")
        except Exception as e:
            raise ValueError(f"Anthropic API调用错误: {str(e)}")
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
    
    def calculate_metrics(self, prompt: str) -> PromptMetrics:
        """计算提示指标"""
        lines = prompt.split('\n')
        words = prompt.split()
        special_chars = [char for char in prompt if not char.isalnum() and not char.isspace()]
        
        return PromptMetrics(
            characters=len(prompt),
            words=len(words),
            lines=len(lines),
            special_chars=list(set(special_chars))
        )
    
    def _validate_messages(self, messages: List[Dict]) -> None:
        """验证消息格式"""
        if not messages:
            raise ValueError("消息列表不能为空")
        
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"消息 {i} 必须是字典格式")
            
            if "role" not in msg or "content" not in msg:
                raise ValueError(f"消息 {i} 必须包含 'role' 和 'content' 字段")
            
            if msg["role"] not in ["system", "user", "assistant"]:
                raise ValueError(f"消息 {i} 的role必须是 'system', 'user' 或 'assistant'")
    
    def _get_provider_from_model(self, model: str) -> str:
        """根据模型名称确定提供商"""
        model_lower = model.lower()
        
        # Anthropic模型
        if any(prefix in model_lower for prefix in ["claude", "sonnet", "haiku", "opus"]):
            return "anthropic"
        
        # OpenAI模型
        if any(prefix in model_lower for prefix in ["gpt", "o1", "o3", "davinci", "curie", "babbage", "ada"]):
            return "openai"
        
        # 默认使用配置中的提供商
        return self.config.default_provider
    
    async def generate_suggestions(self, prompt: str, model: str = "", analysis_context: str = "") -> List[str]:
        """基于AI生成个性化的提示优化建议"""
        
        if not model:
            model = self.config.default_analysis_model
        
        # 构建建议生成的系统提示
        suggestions_system_prompt = """你是一位资深的提示工程专家。请根据给定的提示内容，生成3-5个具体的、可操作的优化建议。

要求：
1. 建议必须针对具体的提示内容，不要给出通用建议
2. 每个建议应该简洁明了，不超过20个字
3. 建议应该涵盖不同方面：结构、清晰度、上下文、输出格式等
4. 建议应该是可操作的，用户能够直接应用
5. 只返回建议列表，每行一个建议，不要其他解释

示例格式：
增加角色定义提高回答专业性
明确输出格式要求避免格式混乱
补充具体示例降低理解门槛"""

        # 构建用户消息
        user_message = f"请为以下提示生成具体的优化建议：\n\n{prompt}"
        
        # 如果有分析上下文，添加到消息中
        if analysis_context:
            user_message += f"\n\n分析上下文：\n{analysis_context}"
        
        messages = [
            {"role": "system", "content": suggestions_system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await self.call_ai(messages, model, 0.3, 300)
            
            # 解析建议
            suggestions = []
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                # 移除可能的序号或标记
                line = line.lstrip('•-*123456789.） ')
                if line and len(line) > 5:  # 过滤掉太短的行
                    suggestions.append(line)
            
            # 确保至少有3个建议，最多5个
            if len(suggestions) < 3:
                # 如果AI生成的建议不够，添加一些通用建议
                fallback_suggestions = [
                    "考虑增加更具体的上下文信息",
                    "明确定义期望的输出格式",
                    "添加示例以提高理解度",
                    "增强指令的清晰度和可操作性",
                    "优化提示结构提高可读性"
                ]
                suggestions.extend(fallback_suggestions[:5-len(suggestions)])
            
            return suggestions[:5]  # 最多返回5个建议
            
        except Exception as e:
            # 如果AI调用失败，返回默认建议
            return [
                "考虑增加更具体的上下文信息",
                "明确定义期望的输出格式",
                "添加示例以提高理解度"
            ] 