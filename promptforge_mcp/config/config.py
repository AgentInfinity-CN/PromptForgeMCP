#!/usr/bin/env python3
"""
配置管理模块
从 .env 文件加载所有配置参数
"""

import os
import logging
from typing import Dict
from dotenv import load_dotenv


class Config:
    """配置管理 - 从 .env 文件加载所有配置参数"""
    def __init__(self, env_file: str = ".env"):
        # 加载 .env 文件
        load_dotenv(env_file, override=True)
        
        # AI 服务提供商配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.default_provider = os.getenv("DEFAULT_AI_PROVIDER", "anthropic")
        
        # 数据库配置
        self.database_path = os.getenv("DATABASE_PATH", "promptforge.db")
        
        # 服务配置
        self.mcp_server_port = int(os.getenv("MCP_SERVER_PORT", "8080"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_prompt_length = int(os.getenv("MAX_PROMPT_LENGTH", "50000"))
        self.analysis_timeout = int(os.getenv("ANALYSIS_TIMEOUT", "30"))
        self.execution_timeout = int(os.getenv("EXECUTION_TIMEOUT", "60"))
        
        # AI 模型配置
        self.default_analysis_model = os.getenv("DEFAULT_ANALYSIS_MODEL", "claude-3-sonnet-20240229")
        self.default_execution_model = os.getenv("DEFAULT_EXECUTION_MODEL", "claude-3-sonnet-20240229")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
        # 安全配置
        self.allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
        # 设置日志级别
        logging.basicConfig(level=getattr(logging, self.log_level.upper()))
        
    def get_available_providers(self) -> Dict[str, bool]:
        """获取可用的AI提供商"""
        return {
            "openai": bool(self.openai_api_key),
            "anthropic": bool(self.anthropic_api_key)
        }
    
    def get_model_for_provider(self, provider: str) -> str:
        """根据提供商获取默认模型"""
        model_map = {
            "openai": self.openai_model,
            "anthropic": self.default_analysis_model
        }
        return model_map.get(provider, self.default_analysis_model) 