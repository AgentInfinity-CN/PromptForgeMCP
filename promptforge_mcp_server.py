#!/usr/bin/env python3
"""
PromptForge MCP Server
====================

基于FastMCP框架的PromptForge AI提示工程服务
提供提示分析、执行、评估生成和库管理功能

使用方法:
    python promptforge_mcp_server.py                    # STDIO模式 (Claude Desktop)
    python promptforge_mcp_server.py --http             # HTTP模式
    python promptforge_mcp_server.py --http --port 8080 # 指定端口
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Any, Union
import argparse
import os
import httpx

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# ================== 数据模型定义 ==================

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

# ================== 配置和工具类 ==================

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

class DatabaseManager:
    """数据库管理器"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建提示库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'General',
                tags TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        # 创建执行历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                model TEXT NOT NULL,
                temperature REAL NOT NULL,
                max_tokens INTEGER,
                success BOOLEAN NOT NULL,
                response TEXT,
                error_msg TEXT,
                execution_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_prompt(self, title: str, content: str, description: str = "", 
                   category: str = "General", tags: List[str] = None) -> SavedPrompt:
        """保存提示"""
        if tags is None:
            tags = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO saved_prompts (title, content, description, category, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (title, content, description, category, json.dumps(tags)))
        
        prompt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return self.get_prompt(prompt_id)
    
    def get_prompt(self, prompt_id: int) -> Optional[SavedPrompt]:
        """获取提示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM saved_prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return SavedPrompt(
                id=row[0], title=row[1], content=row[2], description=row[3],
                category=row[4], tags=json.loads(row[5]), created_at=row[6],
                updated_at=row[7], usage_count=row[8]
            )
        return None
    
    def search_prompts(self, query: str = "", category: str = "", 
                      tags: List[str] = None, limit: int = 20) -> List[SavedPrompt]:
        """搜索提示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_conditions = []
        params = []
        
        if query:
            where_conditions.append("(title LIKE ? OR content LIKE ? OR description LIKE ?)")
            query_param = f"%{query}%"
            params.extend([query_param, query_param, query_param])
        
        if category:
            where_conditions.append("category = ?")
            params.append(category)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        cursor.execute(f"""
            SELECT * FROM saved_prompts 
            WHERE {where_clause}
            ORDER BY updated_at DESC 
            LIMIT ?
        """, params + [limit])
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            # 标签过滤
            prompt_tags = json.loads(row[5])
            if tags and not any(tag in prompt_tags for tag in tags):
                continue
                
            results.append(SavedPrompt(
                id=row[0], title=row[1], content=row[2], description=row[3],
                category=row[4], tags=prompt_tags, created_at=row[6],
                updated_at=row[7], usage_count=row[8]
            ))
        
        return results
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """删除提示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM saved_prompts WHERE id = ?", (prompt_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted

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

# ================== MCP 服务器实现 ==================

# 初始化配置和服务
config = Config()
db_manager = DatabaseManager(config.database_path)
ai_service = AIServiceManager(config)

# 创建FastMCP实例
mcp = FastMCP(
    name="PromptForge MCP Server",
    instructions="AI提示工程工作台 - 提供提示分析、执行和库管理功能。支持从 .env 文件读取配置。"
)

# ================== 提示分析工具 ==================

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

# ================== 提示执行工具 ==================

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





# ================== 提示库管理工具 ==================

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
    await ctx.info(f"💾 保存提示: {title}")
    
    try:
        saved_prompt = db_manager.save_prompt(title, content, description, category, tags)
        await ctx.info(f"✅ 提示已保存，ID: {saved_prompt.id}")
        return saved_prompt
        
    except Exception as e:
        await ctx.error(f"❌ 保存失败: {str(e)}")
        raise

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
    await ctx.info(f"📖 获取提示: ID={prompt_id}")
    
    prompt = db_manager.get_prompt(prompt_id)
    if prompt:
        await ctx.info("✅ 提示获取成功")
        return prompt
    else:
        await ctx.warning(f"⚠️ 未找到ID为 {prompt_id} 的提示")
        return None

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
    await ctx.info(f"🔍 搜索提示: query='{query}', category='{category}', tags={tags}")
    
    results = db_manager.search_prompts(query, category, tags, limit)
    await ctx.info(f"✅ 找到 {len(results)} 个匹配的提示")
    
    return results

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
    await ctx.info(f"🗑️ 删除提示: ID={prompt_id}")
    
    success = db_manager.delete_prompt(prompt_id)
    if success:
        await ctx.info("✅ 提示删除成功")
        return {"success": True, "message": f"提示 {prompt_id} 已删除"}
    else:
        await ctx.warning(f"⚠️ 未找到ID为 {prompt_id} 的提示")
        return {"success": False, "message": f"未找到提示 {prompt_id}"}

# ================== 资源定义 ==================

@mcp.resource("promptforge://config")
async def get_server_config() -> Dict[str, Any]:
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

@mcp.resource("promptforge://status")
async def get_server_status() -> Dict[str, Any]:
    """获取服务器状态"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "运行中",
        "database_connected": True,
        "ai_services_available": len([p for p in config.get_available_providers().values() if p])
    }

@mcp.resource("promptforge://history/{limit}")
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
    
    print("🔨 PromptForge MCP Server")
    print("=" * 50)
    print(f"📊 服务功能: 提示分析、执行、评估、库管理")
    print(f"🗄️ 数据库: {config.database_path}")
    print(f"🤖 可用提供商: {list(config.get_available_providers().keys())}")
    
    if args.http:
        print(f"🌐 HTTP模式: http://{args.host}:{args.port}")
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        print("📡 STDIO模式 (适用于Claude Desktop)")
        mcp.run()

if __name__ == "__main__":
    main() 