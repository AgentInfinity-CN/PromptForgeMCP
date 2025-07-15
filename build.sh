#!/bin/bash
# PromptForge MCP Server - Docker 构建脚本 (Linux/macOS)
# ====================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo
echo "🔨 PromptForge MCP Server - Docker 构建工具"
echo "================================================"

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    print_error "Docker 未安装或未启动"
    print_info "请先安装并启动 Docker"
    exit 1
fi

# 检查 docker-compose 是否可用
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose 未找到"
    print_info "请确保已安装 Docker Compose"
    exit 1
fi

print_success "Docker 环境检查通过"
echo

# 检查 .env 文件
if [ ! -f .env ]; then
    print_warning ".env 文件不存在"
    print_info "正在从模板创建..."
    cp env.template .env
    print_success "已创建 .env 文件，请编辑并填入您的 API 密钥"
    echo
fi

# 显示构建选项
echo "🛠️  请选择构建方式:"
echo "   1. 快速构建 (docker-compose build)"
echo "   2. 完全重构 (docker-compose build --no-cache)"
echo "   3. 构建并启动 (docker-compose up -d --build)"
echo "   4. 仅 Docker 构建 (docker build)"
echo "   5. 退出"
echo

read -p "请输入选择 (1-5): " choice

case $choice in
    1)
        echo
        print_info "执行快速构建..."
        docker-compose build
        print_success "构建完成"
        ;;
    2)
        echo
        print_info "执行完全重构 (无缓存)..."
        docker-compose build --no-cache
        print_success "重构完成"
        ;;
    3)
        echo
        print_info "构建并启动服务..."
        docker-compose up -d --build
        print_success "服务已启动"
        echo
        print_info "服务状态:"
        docker-compose ps
        echo
        print_info "查看日志命令: docker-compose logs -f"
        exit 0
        ;;
    4)
        echo
        print_info "执行 Docker 构建..."
        read -p "请输入镜像标签 (默认: promptforge-mcp:latest): " tag
        if [ -z "$tag" ]; then
            tag="promptforge-mcp:latest"
        fi
        docker build -t "$tag" .
        print_success "构建完成: $tag"
        ;;
    5)
        print_info "退出"
        exit 0
        ;;
    *)
        print_error "无效选择，退出"
        exit 1
        ;;
esac

echo
print_info "构建的镜像:"
docker images | grep promptforge-mcp || print_warning "未找到 promptforge-mcp 镜像"
echo

print_success "构建脚本执行完成" 