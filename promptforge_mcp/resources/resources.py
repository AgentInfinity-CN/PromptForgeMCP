#!/usr/bin/env python3
"""
资源模块
提供MCP资源的实现
"""

from datetime import datetime
from typing import Any, Dict, List
from promptforge_mcp.config.config import Config


async def get_server_config(config: Config) -> Dict[str, Any]:
    """获取服务器配置信息"""
    return {
        "name": "PromptForge MCP Server",
        "version": "1.0.0",
        "available_providers": config.get_available_providers(),
        "default_provider": config.default_provider,
        "database_path": config.database_path,
        "features": ["analysis", "execution", "evaluation", "library"],
        "supported_models": [
            "gpt-4.1", "gpt-4", "gpt-3.5-turbo",
            "claude-3-5-sonnet-20241022", "claude-3-opus-20240229",
            "o3"
        ]
    }


async def get_server_status(config: Config) -> Dict[str, Any]:
    """获取服务器状态"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "运行中",
        "database_connected": True,
        "ai_services_available": len([p for p in config.get_available_providers().values() if p])
    }


async def get_execution_history(limit: int = 50) -> List[Dict[str, Any]]:
    """获取执行历史记录"""
    # 简化实现 - 返回模拟数据
    return [
        {
            "id": i,
            "prompt": f"示例提示 {i}",
            "model": "gpt-4.1",
            "timestamp": datetime.now().isoformat(),
            "success": True
        } for i in range(min(limit, 10))
    ] 