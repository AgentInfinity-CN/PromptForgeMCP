#!/usr/bin/env python3
"""
分析工具模块
提供提示分析相关的MCP工具
"""

import time
from typing import Literal
from fastmcp import Context
from pydantic import Field
from promptforge_mcp.models.models import AnalysisResult
from promptforge_mcp.config.config import Config
from promptforge_mcp.services.ai_service import AIServiceManager


async def analyze_prompt(
    prompt: str = Field(description="要分析的提示文本"),
    model: str = Field(default="", description="使用的AI模型，空值时使用配置默认"),
    analysis_type: Literal["quick", "detailed", "dual"] = Field(default="dual", description="分析类型"),
    config: Config = None,
    ai_service: AIServiceManager = None,
    ctx: Context = None
) -> AnalysisResult:
    """执行提示分析，返回结构化的分析结果"""
    # 如果未指定模型，使用配置中的默认模型
    if not model:
        model = config.default_analysis_model
    
    # 验证提示长度
    if len(prompt) > config.max_prompt_length:
        await ctx.error(f"❌ 提示长度超过限制 ({config.max_prompt_length} 字符)")
        return AnalysisResult(
            success=False,
            quick_report=None,
            detailed_report=None,
            metrics=ai_service.calculate_metrics(prompt),
            suggestions=[],
            error_message=f"提示长度超过限制 ({config.max_prompt_length} 字符)"
        )
    
    await ctx.info(f"🔍 开始分析提示，模式: {analysis_type}, 模型: {model}")
    
    try:
        # 计算基础指标
        metrics = ai_service.calculate_metrics(prompt)
        await ctx.report_progress(25, 100, "计算指标完成")
        
        quick_report = None
        detailed_report = None
        
        if analysis_type in ["quick", "dual"]:
            quick_messages = [
                {"role": "system", "content": "你是提示工程专家，请对提示进行快速分析。"},
                {"role": "user", "content": f"分析这个提示：\n{prompt}"}
            ]
            quick_report = await ai_service.call_ai(quick_messages, model, 0.3, 500)
            await ctx.report_progress(60, 100, "快速分析完成")
        
        if analysis_type in ["detailed", "dual"]:
            detailed_messages = [
                {"role": "system", "content": "你是高级提示工程师，请进行详细的提示分析。"},
                {"role": "user", "content": f"详细分析这个提示：\n{prompt}"}
            ]
            detailed_report = await ai_service.call_ai(detailed_messages, model, 0.5, 1500)
            await ctx.report_progress(90, 100, "详细分析完成")
        
        # 生成AI驱动的个性化优化建议
        await ctx.report_progress(95, 100, "生成优化建议...")
        
        # 将分析报告作为上下文传递给建议生成器
        analysis_context = ""
        if quick_report:
            analysis_context += f"快速分析：{quick_report[:200]}..."
        if detailed_report:
            analysis_context += f"\n详细分析：{detailed_report[:300]}..."
        
        suggestions = await ai_service.generate_suggestions(
            prompt=prompt,
            model=model,
            analysis_context=analysis_context
        )
        
        await ctx.report_progress(100, 100, "分析完成")
        await ctx.info("✅ 提示分析成功完成")
        
        return AnalysisResult(
            success=True,
            quick_report=quick_report,
            detailed_report=detailed_report,
            metrics=metrics,
            suggestions=suggestions
        )
        
    except Exception as e:
        await ctx.error(f"❌ 分析失败: {str(e)}")
        return AnalysisResult(
            success=False,
            quick_report=None,
            detailed_report=None,
            metrics=ai_service.calculate_metrics(prompt),
            suggestions=[],
            error_message=str(e)
        ) 