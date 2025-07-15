# PromptForge MCP Server - Docker 部署指南 🐳

本指南将帮助您使用 Docker 和 Docker Compose 部署 PromptForge MCP 服务。

## 📋 前置要求

- Docker 20.10+
- Docker Compose 1.29+
- 至少 1GB 可用内存
- AI 服务 API 密钥（Anthropic Claude 或 OpenAI GPT）

## 🚀 快速开始

### 1. 准备配置文件

```bash
# 复制环境变量模板
cp env.template .env

# 编辑配置文件，填入您的 API 密钥
nano .env  # 或使用您喜欢的编辑器
```

### 2. 构建镜像

#### 方式一：使用 docker-compose（推荐）

```bash
# 构建并启动服务（自动构建镜像）
docker-compose up -d --build

# 仅构建镜像（不启动）
docker-compose build

# 强制重新构建（忽略缓存）
docker-compose build --no-cache
```

#### 方式二：使用 docker build

```bash
# 基础构建
docker build -t promptforge-mcp:latest .

# 指定标签构建
docker build -t promptforge-mcp:v1.0.0 .

# 无缓存构建
docker build --no-cache -t promptforge-mcp:latest .

# 查看构建的镜像
docker images | grep promptforge-mcp
```

#### 方式三：使用构建脚本

```bash
# Windows
.\build.bat

# Linux/macOS
./build.sh
```

### 3. 启动服务

```bash
# 如果已构建镜像，直接启动
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f promptforge-mcp
```

### 3. 验证部署

```bash
# 检查容器健康状态
docker-compose ps

# 测试服务（如果配置了客户端）
python test_mcp_client.py
```

## ⚙️ 配置说明

### 必需配置

在 `.env` 文件中至少配置以下项目：

```env
# AI 服务 API 密钥（至少配置一个）
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 默认服务提供商
DEFAULT_AI_PROVIDER=anthropic
```

### 可选配置

```env
# 服务端口（默认 8080）
MCP_SERVER_PORT=8080

# 日志级别
LOG_LEVEL=INFO

# 提示长度限制
MAX_PROMPT_LENGTH=50000

# 模型配置
DEFAULT_ANALYSIS_MODEL=claude-3-sonnet-20240229
DEFAULT_EXECUTION_MODEL=claude-3-sonnet-20240229
```

## 📂 数据持久化

### 数据卷说明

- **promptforge_data**: SQLite 数据库和应用数据
- **路径映射**: `./data` (宿主机) ↔ `/data` (容器)

### 备份数据

```bash
# 创建数据备份
docker-compose exec promptforge-mcp sqlite3 /data/promptforge.db ".backup /data/backup.db"

# 复制备份到宿主机
docker cp promptforge-mcp:/data/backup.db ./backup_$(date +%Y%m%d_%H%M%S).db
```

### 恢复数据

```bash
# 停止服务
docker-compose down

# 替换数据库文件
cp your_backup.db ./data/promptforge.db

# 重启服务
docker-compose up -d
```

## 🔧 维护操作

### 查看日志

```bash
# 实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs promptforge-mcp

# 查看最近日志（最后100行）
docker-compose logs --tail=100 promptforge-mcp
```

### 更新镜像

```bash
# 拉取最新代码并重新构建
git pull
docker-compose build --no-cache

# 重启服务
docker-compose down
docker-compose up -d
```

### 清理资源

```bash
# 停止并删除容器
docker-compose down

# 删除数据卷（⚠️ 会丢失所有数据）
docker-compose down -v

# 清理构建缓存
docker system prune -f
```

## 🏗️ 自定义构建

### 修改 Dockerfile

如需自定义镜像，编辑 `Dockerfile`：

```dockerfile
# 示例：添加额外的系统依赖
RUN apt-get update && apt-get install -y \
    your-additional-package \
    && rm -rf /var/lib/apt/lists/*
```

### 修改 docker-compose.yml

```yaml
# 示例：调整资源限制
deploy:
  resources:
    limits:
      memory: 2G  # 增加内存限制
      cpus: '1.0'  # 增加CPU限制
```

## 🐛 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 检查详细错误信息
docker-compose logs promptforge-mcp

# 检查配置文件语法
docker-compose config
```

#### 2. API 密钥错误

确保 `.env` 文件中的 API 密钥正确：

```bash
# 检查环境变量
docker-compose exec promptforge-mcp env | grep API_KEY
```

#### 3. 端口冲突

如果 8080 端口被占用：

```yaml
# 在 docker-compose.yml 中修改端口映射
ports:
  - "8081:8080"  # 使用宿主机 8081 端口
```

#### 4. 权限问题

```bash
# 检查数据目录权限
ls -la ./data/

# 修复权限（如果需要）
sudo chown -R $(id -u):$(id -g) ./data/
```

### 健康检查

容器包含健康检查机制：

```bash
# 检查健康状态
docker-compose ps

# 查看健康检查详情
docker inspect promptforge-mcp | grep -A 10 Health
```

## 🚢 生产环境部署

### 安全最佳实践

1. **使用 Docker Secrets**（Docker Swarm）：

```yaml
secrets:
  anthropic_api_key:
    external: true

services:
  promptforge-mcp:
    secrets:
      - anthropic_api_key
```

2. **设置防火墙规则**：

```bash
# 只允许特定 IP 访问
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

3. **使用反向代理**（Nginx/Traefik）：

```yaml
# 添加到 docker-compose.yml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.promptforge.rule=Host(`promptforge.yourdomain.com`)"
```

### 监控和日志

```yaml
# 添加日志驱动配置
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 📞 支持

如遇问题，请：

1. 检查日志：`docker-compose logs`
2. 验证配置：`docker-compose config`
3. 查看文档：[主项目 README](./PROMPTFORGE_MCP_README.md)
4. 提交 Issue：包含完整的错误日志和环境信息

---

**快乐部署！** 🎉 