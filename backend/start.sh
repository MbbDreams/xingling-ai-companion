#!/bin/bash

# 星灵 AI 伴侣 - 自动化启动脚本
# 功能：检查环境、初始化数据库、启动服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        return 1
    fi
    return 0
}

# 检查 Python 版本
check_python() {
    log_info "检查 Python 版本..."
    if ! check_command python3; then
        log_error "未找到 Python3，请先安装 Python 3.10+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Python 版本: $PYTHON_VERSION"
    
    # 检查版本是否 >= 3.10
    REQUIRED_VERSION="3.10"
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
        log_error "Python 版本需要 >= 3.10，当前版本: $PYTHON_VERSION"
        exit 1
    fi
    log_success "Python 版本检查通过"
}

# 检查虚拟环境
check_venv() {
    log_info "检查虚拟环境..."
    if [ -d ".venv" ]; then
        log_success "找到虚拟环境"
        source .venv/bin/activate
        log_info "已激活虚拟环境"
    else
        log_warn "虚拟环境不存在，正在创建..."
        python3 -m venv .venv
        source .venv/bin/activate
        log_success "虚拟环境创建并激活成功"
    fi
}

# 安装依赖
install_deps() {
    log_info "检查依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt
        log_success "依赖安装完成"
    else
        log_error "未找到 requirements.txt"
        exit 1
    fi
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warn ".env 文件不存在，从 .env.example 复制..."
            cp .env.example .env
            log_warn "请编辑 .env 文件配置您的 API 密钥和数据库连接"
            log_warn "然后重新运行此脚本"
            exit 1
        else
            log_error "未找到 .env 或 .env.example 文件"
            exit 1
        fi
    fi
    log_success "环境变量文件存在"
}

# 检查 PostgreSQL
check_postgres() {
    log_info "检查 PostgreSQL..."
    
    # 尝试从 .env 读取数据库连接信息
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # 检查 Docker 中的 PostgreSQL
    if docker ps | grep -q "xingling-postgres\|pgvector"; then
        log_success "PostgreSQL (Docker) 正在运行"
        return 0
    fi
    
    # 检查本地 PostgreSQL
    if check_command pg_isready; then
        if pg_isready -h localhost -p 5433 &>/dev/null || pg_isready -h localhost -p 5432 &>/dev/null; then
            log_success "PostgreSQL (本地) 正在运行"
            return 0
        fi
    fi
    
    log_warn "PostgreSQL 未运行"
    log_info "尝试启动 PostgreSQL (Docker)..."
    
    # 尝试启动 Docker PostgreSQL
    if check_command docker; then
        docker run -d \
            --name xingling-postgres \
            -e POSTGRES_USER=xingling \
            -e POSTGRES_PASSWORD=xingling_dev \
            -e POSTGRES_DB=xingling_ai \
            -p 5433:5432 \
            ankane/pgvector:latest 2>/dev/null || true
        
        # 等待 PostgreSQL 启动
        log_info "等待 PostgreSQL 启动..."
        sleep 3
        
        if docker ps | grep -q "xingling-postgres"; then
            log_success "PostgreSQL (Docker) 启动成功"
            return 0
        fi
    fi
    
    log_error "无法启动 PostgreSQL，请手动安装并启动"
    log_info "安装指南:"
    log_info "  macOS: brew install postgresql@14 && brew install pgvector"
    log_info "  Docker: docker run -d --name xingling-postgres -e POSTGRES_USER=xingling -e POSTGRES_PASSWORD=xingling_dev -e POSTGRES_DB=xingling_ai -p 5433:5432 ankane/pgvector:latest"
    exit 1
}

# 检查 Redis (可选)
check_redis() {
    log_info "检查 Redis (可选)..."
    
    if docker ps | grep -q "xingling-redis\|redis"; then
        log_success "Redis (Docker) 正在运行"
        return 0
    fi
    
    if check_command redis-cli; then
        if redis-cli ping &>/dev/null; then
            log_success "Redis (本地) 正在运行"
            return 0
        fi
    fi
    
    log_warn "Redis 未运行，尝试启动..."
    
    if check_command docker; then
        docker run -d \
            --name xingling-redis \
            -p 6380:6379 \
            redis:7-alpine 2>/dev/null || true
        
        sleep 2
        
        if docker ps | grep -q "xingling-redis"; then
            log_success "Redis (Docker) 启动成功"
            return 0
        fi
    fi
    
    log_warn "Redis 启动失败，将继续运行（部分功能可能受限）"
}

# 初始化数据库
init_database() {
    log_info "检查数据库初始化..."
    
    if [ -f "init_db.py" ]; then
        log_info "运行数据库初始化（非交互模式）..."
        python init_db.py --force
        log_success "数据库初始化完成"
    else
        log_warn "未找到 init_db.py，跳过数据库初始化"
    fi
}

# 检查 API 密钥
check_api_keys() {
    log_info "检查 API 密钥..."
    
    if [ -f ".env" ]; then
        # 检查 DeepSeek API Key
        if grep -q "DEEPSEEK_API_KEY=your-" .env || grep -q "DEEPSEEK_API_KEY=$" .env; then
            log_warn "DeepSeek API Key 未配置"
            log_info "请访问 https://platform.deepseek.com/api_keys 获取 API Key"
        else
            log_success "DeepSeek API Key 已配置"
        fi
        
        # 检查 Embedding API Key
        if grep -q "EMBEDDING_API_KEY=your-" .env || grep -q "EMBEDDING_API_KEY=$" .env; then
            log_warn "Embedding API Key 未配置"
            log_info "请访问 https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey 获取 API Key"
        else
            log_success "Embedding API Key 已配置"
        fi
    fi
}

# 显示启动信息
show_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           星灵 AI 伴侣 (Xingling AI Companion)                ║"
    echo "║                                                              ║"
    echo "║              一个有记忆、有温度、会成长的 AI 伴侣              ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

# 启动服务
start_server() {
    log_info "启动服务..."
    echo ""
    echo "服务将在以下地址启动:"
    echo "  - API 服务: http://localhost:8000"
    echo "  - API 文档: http://localhost:8000/docs"
    echo "  - 健康检查: http://localhost:8000/health"
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo ""
    
    python app/main.py
}

# 清理函数
cleanup() {
    echo ""
    log_info "正在关闭服务..."
    deactivate 2>/dev/null || true
    exit 0
}

# 设置清理钩子
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    show_banner
    
    log_info "开始启动星灵 AI 伴侣..."
    echo ""
    
    # 执行检查
    check_python
    check_venv
    install_deps
    check_env
    check_postgres
    check_redis
    init_database
    check_api_keys
    
    echo ""
    log_success "所有检查通过！"
    echo ""
    
    # 启动服务
    start_server
}

# 解析命令行参数
case "${1:-}" in
    --help|-h)
        echo "星灵 AI 伴侣 - 自动化启动脚本"
        echo ""
        echo "用法: ./start.sh [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h     显示帮助信息"
        echo "  --init-only    只初始化环境，不启动服务"
        echo "  --skip-checks  跳过环境检查，直接启动服务"
        echo ""
        echo "示例:"
        echo "  ./start.sh              # 完整启动流程"
        echo "  ./start.sh --init-only  # 只初始化环境"
        exit 0
        ;;
    --init-only)
        show_banner
        check_python
        check_venv
        install_deps
        check_env
        check_postgres
        check_redis
        init_database
        log_success "环境初始化完成！"
        exit 0
        ;;
    --skip-checks)
        show_banner
        source .venv/bin/activate 2>/dev/null || true
        start_server
        ;;
    *)
        main
        ;;
esac
