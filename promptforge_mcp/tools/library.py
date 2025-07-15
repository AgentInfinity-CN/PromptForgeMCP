#!/usr/bin/env python3
"""
库管理工具模块
提供提示库管理相关的MCP工具
"""

from typing import Dict, List, Optional, Union
from fastmcp import Context
from pydantic import Field
from promptforge_mcp.models.models import SavedPrompt
from promptforge_mcp.database.database import DatabaseManager


async def save_prompt(
    title: str = Field(description="提示标题"),
    content: str = Field(description="提示内容"),
    description: str = Field(default="", description="提示描述"),
    category: str = Field(default="General", description="分类"),
    tags: List[str] = Field(default_factory=list, description="标签"),
    db_manager: DatabaseManager = None,
    ctx: Context = None
) -> SavedPrompt:
    """保存新的提示到库中"""
    await ctx.info(f"💾 保存提示: {title}")
    
    try:
        saved_prompt = db_manager.save_prompt(title, content, description, category, tags)
        await ctx.info(f"✅ 提示已保存，ID: {saved_prompt.id}")
        return saved_prompt
        
    except Exception as e:
        await ctx.error(f"❌ 保存失败: {str(e)}")
        raise


async def get_saved_prompt(
    prompt_id: int = Field(description="提示ID"),
    db_manager: DatabaseManager = None,
    ctx: Context = None
) -> Optional[SavedPrompt]:
    """根据ID获取提示"""
    await ctx.info(f"📖 获取提示: ID={prompt_id}")
    
    prompt = db_manager.get_prompt(prompt_id)
    if prompt:
        await ctx.info("✅ 提示获取成功")
        return prompt
    else:
        await ctx.warning(f"⚠️ 未找到ID为 {prompt_id} 的提示")
        return None


async def search_prompts(
    query: str = Field(default="", description="搜索关键词"),
    category: str = Field(default="", description="筛选分类"),
    tags: List[str] = Field(default_factory=list, description="筛选标签"),
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制"),
    db_manager: DatabaseManager = None,
    ctx: Context = None
) -> List[SavedPrompt]:
    """搜索和筛选已保存的提示"""
    await ctx.info(f"🔍 搜索提示: query='{query}', category='{category}', tags={tags}")
    
    results = db_manager.search_prompts(query, category, tags, limit)
    await ctx.info(f"✅ 找到 {len(results)} 个匹配的提示")
    
    return results


async def delete_prompt(
    prompt_id: int = Field(description="要删除的提示ID"),
    db_manager: DatabaseManager = None,
    ctx: Context = None
) -> Dict[str, Union[bool, str]]:
    """删除指定ID的提示"""
    await ctx.info(f"🗑️ 删除提示: ID={prompt_id}")
    
    success = db_manager.delete_prompt(prompt_id)
    if success:
        await ctx.info("✅ 提示删除成功")
        return {"success": True, "message": f"提示 {prompt_id} 已删除"}
    else:
        await ctx.warning(f"⚠️ 未找到ID为 {prompt_id} 的提示")
        return {"success": False, "message": f"未找到提示 {prompt_id}"} 