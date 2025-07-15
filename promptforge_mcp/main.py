#!/usr/bin/env python3
"""
PromptForge MCP Server - 主入口文件
====================

基于FastMCP框架的PromptForge AI提示工程服务
提供提示分析、执行、评估生成和库管理功能

使用方法:
    python mcp/main.py                    # STDIO模式 (Claude Desktop)
    python mcp/main.py --http             # HTTP模式
    python mcp/main.py --http --port 8080 # 指定端口
"""

import argparse
import logging
from fastmcp import FastMCP, Context
from pydantic import Field
from typing import Dict, List, Optional, Union, Any, Literal

# 导入配置和服务
from promptforge_mcp.config.config import Config
from promptforge_mcp.database.database import DatabaseManager
from promptforge_mcp.services.ai_service import AIServiceManager

# 导入数据模型
from promptforge_mcp.models.models import AnalysisResult, ExecutionResult, SavedPrompt

# 导入工具函数
from promptforge_mcp.tools.analysis import analyze_prompt as analyze_prompt_func
from promptforge_mcp.tools.execution import execute_prompt as execute_prompt_func
from promptforge_mcp.tools.library import (
    save_prompt as save_prompt_func,
    get_saved_prompt as get_saved_prompt_func,
    search_prompts as search_prompts_func,
    delete_prompt as delete_prompt_func
)

# 导入资源函数
from promptforge_mcp.resources.resources import (
    get_server_config as get_server_config_func,
    get_server_status as get_server_status_func,
    get_execution_history as get_execution_history_func
)

# ================== 初始化服务 ==================

# 初始化配置和服务
config = Config()
db_manager = DatabaseManager(config.database_path)
ai_service = AIServiceManager(config)

# 创建FastMCP实例
mcp = FastMCP(
    name="PromptForge MCP Server",
    instructions="AI提示工程工作台 - 提供提示分析、执行和库管理功能。支持从 .env 文件读取配置。"
)

# ================== 注册工具 ==================

@mcp.tool(
    name="analyze_prompt",
    description="对提示进行全面分析，包括快速和详细两种报告",
    tags={"analysis", "core"}
)
async def analyze_prompt(
    prompt: str = Field(description="要分析的提示文本"),
    model: str = Field(default="", description="使用的AI模型，空值时使用配置默认"),
    analysis_type: Literal["quick", "detailed", "dual"] = Field(default="dual", description="分析类型"),
    ctx: Context = None
) -> AnalysisResult:
    """执行提示分析，返回结构化的分析结果"""
    return await analyze_prompt_func(
        prompt=prompt,
        model=model,
        analysis_type=analysis_type,
        config=config,
        ai_service=ai_service,
        ctx=ctx
    )


@mcp.tool(
    name="execute_prompt",
    description="执行提示并获取AI响应",
    tags={"execution", "core"}
)
async def execute_prompt(
    prompt: str = Field(description="要执行的提示"),
    model: str = Field(default="", description="AI模型名称，空值时使用配置默认"),
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="创造性温度参数"),
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="最大输出令牌数"),
    variables: Optional[Dict[str, str]] = Field(default=None, description="提示变量替换"),
    ctx: Context = None
) -> ExecutionResult:
    """执行单个模型的提示"""
    return await execute_prompt_func(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        variables=variables,
        config=config,
        ai_service=ai_service,
        ctx=ctx
    )


@mcp.tool(
    name="save_prompt",
    description="保存提示到库中",
    tags={"library", "create"}
)
async def save_prompt(
    title: str = Field(description="提示标题"),
    content: str = Field(description="提示内容"),
    description: str = Field(default="", description="提示描述"),
    category: str = Field(default="General", description="分类"),
    tags: List[str] = Field(default_factory=list, description="标签"),
    ctx: Context = None
) -> SavedPrompt:
    """保存新的提示到库中"""
    return await save_prompt_func(
        title=title,
        content=content,
        description=description,
        category=category,
        tags=tags,
        db_manager=db_manager,
        ctx=ctx
    )


@mcp.tool(
    name="get_saved_prompt",
    description="获取已保存的提示",
    tags={"library", "read"}
)
async def get_saved_prompt(
    prompt_id: int = Field(description="提示ID"),
    ctx: Context = None
) -> Optional[SavedPrompt]:
    """根据ID获取提示"""
    return await get_saved_prompt_func(
        prompt_id=prompt_id,
        db_manager=db_manager,
        ctx=ctx
    )


@mcp.tool(
    name="search_prompts",
    description="搜索提示库",
    tags={"library", "search"}
)
async def search_prompts(
    query: str = Field(default="", description="搜索关键词"),
    category: str = Field(default="", description="筛选分类"),
    tags: List[str] = Field(default_factory=list, description="筛选标签"),
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制"),
    ctx: Context = None
) -> List[SavedPrompt]:
    """搜索和筛选已保存的提示"""
    return await search_prompts_func(
        query=query,
        category=category,
        tags=tags,
        limit=limit,
        db_manager=db_manager,
        ctx=ctx
    )


@mcp.tool(
    name="delete_prompt",
    description="删除已保存的提示",
    tags={"library", "delete"}
)
async def delete_prompt(
    prompt_id: int = Field(description="要删除的提示ID"),
    ctx: Context = None
) -> Dict[str, Union[bool, str]]:
    """删除指定ID的提示"""
    return await delete_prompt_func(
        prompt_id=prompt_id,
        db_manager=db_manager,
        ctx=ctx
    )

# ================== 注册资源 ==================

@mcp.resource("promptforge://config")
async def get_server_config() -> Dict[str, Any]:
    """获取服务器配置信息"""
    return await get_server_config_func(config)


@mcp.resource("promptforge://status")
async def get_server_status() -> Dict[str, Any]:
    """获取服务器状态"""
    return await get_server_status_func(config)


@mcp.resource("promptforge://history/{limit}")
async def get_execution_history(limit: int = 50) -> List[Dict[str, Any]]:
    """获取执行历史记录"""
    return await get_execution_history_func(limit)

# ================== 主程序 ==================

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="PromptForge MCP Server")
    parser.add_argument("--http", action="store_true", help="使用HTTP传输模式")
    parser.add_argument("--port", type=int, default=config.mcp_server_port, help="HTTP端口号")
    parser.add_argument("--host", default="localhost", help="HTTP主机地址")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 使用配置中的调试设置，但命令行参数可以覆盖
    debug_mode = args.debug or config.debug_mode
    
    # 日志已在Config类中配置，这里只在需要时覆盖
    if debug_mode:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("PromptForge MCP Server")
    print("=" * 50)
    print(f"服务功能: 提示分析、执行、评估、库管理")
    print(f"数据库: {config.database_path}")
    print(f"可用提供商: {list(config.get_available_providers().keys())}")
    
    if args.http:
        print(f"HTTP模式: http://{args.host}:{args.port}")
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        print("STDIO模式 (适用于Claude Desktop)")
        mcp.run()


if __name__ == "__main__":
    main() 