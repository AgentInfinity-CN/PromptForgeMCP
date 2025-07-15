# PromptForge MCP Server 🔨

基于 FastMCP 框架的专业 AI 提示工程服务，为智能体提供强大的提示分析、执行、评估和管理功能。

## ✨ 核心功能

### 🔍 提示分析

- **智能分析**: 快速/详细/双重分析模式，基于真实AI模型分析
- **指标统计**: 字符数、词数、特殊字符分析
- **AI驱动建议**: 基于提示内容生成个性化优化建议
- **上下文感知**: 建议生成器考虑分析结果上下文
- **多样化建议**: 涵盖结构、清晰度、格式、上下文等多个维度

### ⚡ 提示执行

- **真实AI调用**: 集成OpenAI和Anthropic API，支持真实模型调用
- **智能路由**: 根据模型名称自动选择合适的AI提供商
- **参数控制**: 支持温度、令牌数等参数精确控制
- **变量替换**: 动态替换提示中的占位符
- **配置驱动**: 支持从 .env 文件读取默认配置
- **错误处理**: 完善的错误处理和输入验证机制

### 📚 提示库管理

- **CRUD操作**: 保存、获取、搜索、删除提示
- **分类标签**: 灵活的分类和标签系统
- **搜索过滤**: 基于关键词、分类、标签的智能搜索

## 📁 项目结构

项目采用模块化设计，清晰分离各个功能模块：

```
prompt-forge/
├── promptforge_mcp/                # MCP服务主包
│   ├── __init__.py                 # 包初始化
│   ├── main.py                     # MCP服务器主入口
│   ├── config/                     # 配置管理模块
│   │   ├── __init__.py
│   │   └── config.py               # 环境变量和配置管理
│   ├── models/                     # 数据模型模块
│   │   ├── __init__.py
│   │   └── models.py               # Pydantic数据模型定义
│   ├── database/                   # 数据库管理模块
│   │   ├── __init__.py
│   │   └── database.py             # SQLite数据库操作
│   ├── services/                   # 业务服务模块
│   │   ├── __init__.py
│   │   └── ai_service.py           # AI服务管理（OpenAI/Anthropic）
│   ├── tools/                      # MCP工具模块
│   │   ├── __init__.py
│   │   ├── analysis.py             # 提示分析工具
│   │   ├── execution.py            # 提示执行工具
│   │   └── library.py              # 提示库管理工具
│   └── resources/                  # MCP资源模块
│       ├── __init__.py
│       └── resources.py            # MCP资源实现
├── test_mcp_client.py              # 测试客户端
├── pyproject.toml                  # uv项目配置和依赖管理
└── env.template                    # 环境变量配置模板
```

### 🏗️ 架构设计

- **配置层**: 统一的环境变量管理，支持 .env 文件配置
- **数据层**: SQLite数据库，提供提示库和执行历史存储
- **服务层**: AI服务管理，支持多提供商和智能路由
- **工具层**: 模块化的MCP工具实现，每个功能独立封装
- **资源层**: MCP资源端点，提供服务状态和配置信息

## ⚙️ 配置说明

### 环境变量配置

PromptForge MCP 支持通过 `.env` 文件进行配置管理，提供更好的安全性和灵活性。

#### 1. 创建配置文件

将 `env.template` 复制为 `.env` 并填入您的配置：

```bash
cp env.template .env
```

#### 2. 主要配置项

```env
# AI 服务配置
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_AI_PROVIDER=anthropic

# 服务配置
MCP_SERVER_PORT=8080
MAX_PROMPT_LENGTH=50000
LOG_LEVEL=INFO

# 模型配置
DEFAULT_ANALYSIS_MODEL=claude-3-sonnet-20240229
DEFAULT_EXECUTION_MODEL=claude-3-sonnet-20240229
```

📋 完整的配置选项请参考 `env.template` 文件。

## 🤖 支持的AI模型

### Anthropic Claude 系列
- **claude-3-7-sonnet-20250219** (默认)
- claude-3-5-sonnet-20241022
- claude-3-haiku-20240307
- claude-3-opus-20240229

### OpenAI GPT 系列
- gpt-4-turbo-preview
- gpt-4
- gpt-3.5-turbo
- o1-preview (支持)
- o3 (支持)

### 自动模型选择
服务会根据模型名称自动选择合适的API提供商：
- `claude*`, `sonnet*`, `haiku*`, `opus*` → Anthropic
- `gpt*`, `o1*`, `o3*` → OpenAI  
- 其他模型使用 `DEFAULT_AI_PROVIDER` 配置

## 🧠 智能建议系统

PromptForge MCP 配备了先进的AI驱动建议系统，能够根据具体的提示内容生成个性化的优化建议。

### 🔧 建议生成原理

1. **内容分析**: AI首先分析提示的结构、内容和意图
2. **上下文理解**: 结合快速/详细分析的结果作为上下文
3. **个性化生成**: 针对具体提示生成3-5个可操作的优化建议
4. **多维度覆盖**: 建议涵盖结构、清晰度、上下文、输出格式等方面

### 💡 建议特点

- **针对性强**: 每个建议都针对具体的提示内容，而非通用建议
- **可操作性**: 建议简洁明了，用户可以直接应用
- **多样化**: 从不同角度提供优化方向
- **智能降级**: 如果AI生成失败，自动提供备用建议

### 📊 建议示例

```json
{
  "suggestions": [
    "明确定义用户角色和专业背景",
    "添加具体的输出格式要求",
    "补充相关示例提高理解度",
    "增加约束条件避免偏离主题"
  ]
}
```

## 🚀 快速开始

### 1. 安装 uv (如果尚未安装)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

### 2. 初始化项目并安装依赖

```bash
# 同步安装所有依赖
uv sync

# 或者手动安装
uv venv
uv pip install -e .
```

### 3. 配置环境变量

```bash
# AI提供商API密钥 (至少配置一个)
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"  

# 可选配置
export DEFAULT_AI_PROVIDER="anthropic"  # 默认提供商
```

### 4. 启动服务

#### STDIO 模式 (Claude Desktop)

```bash
uv run -m promptforge_mcp.main
```

#### HTTP 模式 (其他客户端)

```bash
uv run -m promptforge_mcp.main --http --port 8080
```

#### 调试模式

```bash
uv run -m promptforge_mcp.main --debug
```

#### 使用入口点脚本 (安装后)

```bash
# 安装到当前环境
uv pip install -e .

# 然后可以直接使用
promptforge-mcp --http --port 8080
```

#### 或者使用 uv 直接运行

```bash
# 直接运行（推荐）
uv run promptforge-mcp --http --port 8080
```

## 🛠️ 工具列表

### 🔍 分析工具

| 工具名称           | 描述                              | 参数                         |
| ------------------ | --------------------------------- | ---------------------------- |
| `analyze_prompt` | 智能提示分析 (支持快速/详细/双重模式) | prompt, model*, analysis_type |

*model 参数为可选，空值时使用 .env 中配置的默认模型

### ⚡ 执行工具

| 工具名称          | 描述           | 参数                                              |
| ----------------- | -------------- | ------------------------------------------------- |
| `execute_prompt` | 智能提示执行 | prompt, model*, temperature, max_tokens, variables |

*model 参数为可选，空值时使用 .env 中配置的默认模型

### 库管理工具

| 工具名称             | 描述     | 参数                                        |
| -------------------- | -------- | ------------------------------------------- |
| `save_prompt`      | 保存提示 | title, content, description, category, tags |
| `get_saved_prompt` | 获取提示 | prompt_id                                   |
| `search_prompts`   | 搜索提示 | query, category, tags, limit                |
| `delete_prompt`    | 删除提示 | prompt_id                                   |

## 📁 资源列表

| 资源URI                           | 描述       | 内容                   |
| --------------------------------- | ---------- | ---------------------- |
| `promptforge://config`          | 服务器配置 | 提供商、模型、功能列表 |
| `promptforge://status`          | 服务器状态 | 健康状态、运行时间     |
| `promptforge://history/{limit}` | 执行历史   | 最近的执行记录         |

## 💡 使用示例

### 🔍 智能分析

```python
# 全面分析 (使用配置默认模型)
result = await client.call_tool("analyze_prompt", {
    "prompt": "请总结以下文本的主要观点：", 
    "analysis_type": "dual"  # 快速+详细双重分析
})

# 指定特定模型进行分析
result = await client.call_tool("analyze_prompt", {
    "prompt": "分析这个营销文案的有效性",
    "model": "claude-3-7-sonnet-20250219",
    "analysis_type": "quick"  # 仅快速分析
})

# 分析结果包含个性化建议
# result.data.suggestions 包含根据提示内容生成的具体建议
# 例如：["增加目标受众定义", "补充具体产品信息", "明确营销目标和KPI"]
```

### ⚡ 智能执行

```python
# 使用默认配置执行
result = await client.call_tool("execute_prompt", {
    "prompt": "你好，我的名字是{name}，请介绍一下{topic}",
    "variables": {"name": "张三", "topic": "人工智能"},
    "temperature": 0.7,
    "max_tokens": 1000
})

# 指定特定模型执行
result = await client.call_tool("execute_prompt", {
    "prompt": "写一首关于春天的诗",
    "model": "gpt-4-turbo-preview",
    "temperature": 0.8
})
```

### 保存和搜索提示

```python
# 保存提示
await client.call_tool("save_prompt", {
    "title": "技术文档总结",
    "content": "请总结这份技术文档的关键要点：{document}",
    "description": "用于技术文档的快速总结",
    "category": "Documentation",
    "tags": ["summary", "technical", "documentation"]
})

# 搜索提示
results = await client.call_tool("search_prompts", {
    "query": "总结",
    "category": "Documentation", 
    "tags": ["technical"],
    "limit": 10
})
```

## 🔧 配置选项

### 环境变量

- `ANTHROPIC_API_KEY`: Anthropic API密钥
- `OPENAI_API_KEY`: OpenAI API密钥
- `DEFAULT_AI_PROVIDER`: 默认AI提供商 (anthropic/openai)

### 命令行参数

- `--http`: 启用HTTP传输模式
- `--port PORT`: HTTP端口号 (默认8000)
- `--host HOST`: HTTP主机地址 (默认localhost)
- `--debug`: 启用调试模式

## 📊 数据存储

服务使用SQLite数据库存储：

- **提示库**: `saved_prompts` 表
- **执行历史**: `execution_history` 表
- **数据库文件**: `promptforge_mcp.db`

## 🧪 开发和测试

### 运行测试

```bash
# 安装开发依赖
uv sync --extra dev

# 运行测试
uv run pytest

# 运行测试脚本
uv run test_mcp_client.py
```

### 代码质量

```bash
# 代码格式化
uv run black .

# 代码检查
uv run ruff check .

# 类型检查 (如果配置了mypy)
uv run mypy .
```

### 添加新依赖

```bash
# 添加生产依赖
uv add package-name

# 添加开发依赖  
uv add --dev package-name

# 添加特定版本
uv add "package-name>=1.0.0,<2.0.0"
```

## 🔌 集成方式

### Claude Desktop

1. 将服务添加到Claude Desktop配置
2. 使用STDIO模式连接
3. 通过MCP协议调用工具

### 自定义客户端

1. 使用HTTP模式启动服务
2. 通过FastMCP客户端连接
3. 调用提供的工具和资源

## 🛡️ 错误处理

- **统一错误响应**: 所有工具返回结构化错误信息
- **日志记录**: 详细的执行日志和错误跟踪
- **优雅降级**: API调用失败时的备用方案

## 📈 性能特性

- **异步执行**: 支持高并发操作
- **连接池**: 高效的HTTP客户端连接管理
- **缓存机制**: 智能的结果缓存策略
- **进度报告**: 实时的执行进度反馈

## 🤝 扩展开发

### 添加新工具

```python
@mcp.tool(
    name="custom_tool",
    description="自定义工具描述",
    tags={"custom"}
)
async def custom_tool(param: str, ctx: Context = None) -> dict:
    await ctx.info("执行自定义工具")
    # 实现逻辑
    return {"result": "success"}
```

### 添加新资源

```python
@mcp.resource("promptforge://custom/{param}")
async def custom_resource(param: str) -> dict:
    return {"data": f"自定义资源数据: {param}"}
```

## 📄 许可证

基于原PromptForge项目的GPLv3许可证。

---

**让AI提示工程从艺术变为科学** 🎯
