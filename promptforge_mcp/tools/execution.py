#!/usr/bin/env python3
"""
执行工具模块
提供提示执行相关的MCP工具
"""

import time
from typing import Dict, Optional
from fastmcp import Context
from pydantic import Field
from promptforge_mcp.models.models import ExecutionResult
from promptforge_mcp.config.config import Config
from promptforge_mcp.services.ai_service import AIServiceManager


async def execute_prompt(
    prompt: str = Field(description="要执行的提示"),
    model: str = Field(default="", description="AI模型名称，空值时使用配置默认"),
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="创造性温度参数"),
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="最大输出令牌数"),
    variables: Optional[Dict[str, str]] = Field(default=None, description="提示变量替换"),
    config: Config = None,
    ai_service: AIServiceManager = None,
    ctx: Context = None
) -> ExecutionResult:
    """执行单个模型的提示"""
    # 如果未指定模型，使用配置中的默认模型
    if not model:
        model = config.default_execution_model
    
    # 验证提示长度
    if len(prompt) > config.max_prompt_length:
        await ctx.error(f"❌ 提示长度超过限制 ({config.max_prompt_length} 字符)")
        return ExecutionResult(
            success=False,
            response="",
            model=model,
            execution_time=0,
            token_usage={},
            error_message=f"提示长度超过限制 ({config.max_prompt_length} 字符)"
        )
    
    await ctx.info(f"⚡ 执行提示，模型: {model}")
    start_time = time.time()
    
    try:
        # 变量替换
        if variables:
            for key, value in variables.items():
                prompt = prompt.replace(f"{{{key}}}", value)
            await ctx.info(f"🔄 已替换 {len(variables)} 个变量")
        
        await ctx.report_progress(25, 100, "准备执行...")
        
        # 执行AI调用
        messages = [{"role": "user", "content": prompt}]
        response = await ai_service.call_ai(messages, model, temperature, max_tokens)
        
        execution_time = time.time() - start_time
        await ctx.report_progress(100, 100, "执行完成")
        await ctx.info(f"✅ 执行成功，耗时: {execution_time:.2f}秒")
        
        return ExecutionResult(
            success=True,
            response=response,
            model=model,
            execution_time=execution_time,
            token_usage={"input": len(prompt.split()), "output": len(response.split())},
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        await ctx.error(f"❌ 执行失败: {str(e)}")
        
        return ExecutionResult(
            success=False,
            response="",
            model=model,
            execution_time=execution_time,
            token_usage={},
            error_message=str(e)
        ) 