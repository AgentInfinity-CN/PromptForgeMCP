#!/usr/bin/env python3
"""
数据模型定义
使用Pydantic进行数据验证和序列化
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class PromptMetrics(BaseModel):
    """提示指标统计"""
    characters: int = Field(description="字符数")
    words: int = Field(description="词数")
    lines: int = Field(description="行数")
    special_chars: List[str] = Field(description="特殊字符")


class AnalysisResult(BaseModel):
    """分析结果模型"""
    success: bool = Field(description="分析是否成功")
    quick_report: Optional[str] = Field(description="快速分析报告")
    detailed_report: Optional[str] = Field(description="详细分析报告")
    metrics: PromptMetrics = Field(description="提示指标统计")
    suggestions: List[str] = Field(description="优化建议")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class ExecutionResult(BaseModel):
    """执行结果模型"""
    success: bool = Field(description="执行是否成功")
    response: str = Field(description="AI模型响应")
    model: str = Field(description="使用的模型")
    execution_time: float = Field(description="执行时间(秒)")
    token_usage: Dict[str, int] = Field(description="令牌使用统计")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class SavedPrompt(BaseModel):
    """保存的提示"""
    id: int = Field(description="提示ID")
    title: str = Field(description="提示标题")
    content: str = Field(description="提示内容")
    description: str = Field(description="描述信息")
    category: str = Field(description="分类")
    tags: List[str] = Field(description="标签列表")
    created_at: str = Field(description="创建时间")
    updated_at: str = Field(description="更新时间")
    usage_count: int = Field(description="使用次数") 