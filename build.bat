@echo off
REM PromptForge MCP Server - Docker 构建脚本 (Windows)
REM ====================================================

echo.
echo 🔨 PromptForge MCP Server - Docker 构建工具
echo ================================================

REM 检查 Docker 是否可用
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Docker 未安装或未启动
    echo    请先安装并启动 Docker Desktop
    pause
    exit /b 1
)

REM 检查 docker-compose 是否可用
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: docker-compose 未找到
    echo    请确保已安装 Docker Compose
    pause
    exit /b 1
)

echo ✅ Docker 环境检查通过
echo.

REM 检查 .env 文件
if not exist .env (
    echo ⚠️  警告: .env 文件不存在
    echo    正在从模板创建...
    copy env.template .env >nul
    echo ✅ 已创建 .env 文件，请编辑并填入您的 API 密钥
    echo.
)

REM 显示构建选项
echo 🛠️  请选择构建方式:
echo    1. 快速构建 (docker-compose build)
echo    2. 完全重构 (docker-compose build --no-cache)
echo    3. 构建并启动 (docker-compose up -d --build)
echo    4. 仅 Docker 构建 (docker build)
echo    5. 退出
echo.

set /p choice="请输入选择 (1-5): "

if "%choice%"=="1" goto quick_build
if "%choice%"=="2" goto full_rebuild
if "%choice%"=="3" goto build_and_start
if "%choice%"=="4" goto docker_build
if "%choice%"=="5" goto end
echo ❌ 无效选择，退出
goto end

:quick_build
echo.
echo 🚀 执行快速构建...
docker-compose build
if %errorlevel% neq 0 (
    echo ❌ 构建失败
    pause
    exit /b 1
)
echo ✅ 构建完成
goto show_images

:full_rebuild
echo.
echo 🔄 执行完全重构 (无缓存)...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo ❌ 构建失败
    pause
    exit /b 1
)
echo ✅ 重构完成
goto show_images

:build_and_start
echo.
echo 🚀 构建并启动服务...
docker-compose up -d --build
if %errorlevel% neq 0 (
    echo ❌ 构建或启动失败
    pause
    exit /b 1
)
echo ✅ 服务已启动
echo.
echo 📊 服务状态:
docker-compose ps
echo.
echo 📝 查看日志命令: docker-compose logs -f
goto end

:docker_build
echo.
echo 🏗️  执行 Docker 构建...
set /p tag="请输入镜像标签 (默认: promptforge-mcp:latest): "
if "%tag%"=="" set tag=promptforge-mcp:latest

docker build -t %tag% .
if %errorlevel% neq 0 (
    echo ❌ 构建失败
    pause
    exit /b 1
)
echo ✅ 构建完成: %tag%
goto show_images

:show_images
echo.
echo 📦 构建的镜像:
docker images | findstr promptforge-mcp
echo.

:end
echo 🎉 构建脚本执行完成
pause 