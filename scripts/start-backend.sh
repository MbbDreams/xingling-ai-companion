#!/bin/bash

# 星灵 AI 伴侣 - 后端启动脚本
# 用法: ./start-backend.sh [dev|prod]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# 环境模式
MODE="${1:-dev}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Python 版本
check_python() {
    log_info "检查 Python 版本..."
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python3，请先安装 Python 3.10+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_success "Python 版本: $PYTHON_VERSION"
}

# 检查虚拟环境
check_venv() {
    log_info "检查虚拟环境..."
    if [ ! -d "$BACKEND_DIR/.venv" ]; then
        log_warning "虚拟环境不存在，正在创建..."
        cd "$BACKEND_DIR"
        python3 -m venv .venv
        log_success "虚拟环境创建完成"
    else
        log_success "虚拟环境已存在"
    fi
}

# 激活虚拟环境
activate_venv() {
    log_info "激活虚拟环境..."
    source "$BACKEND_DIR/.venv/bin/activate"
    log_success "虚拟环境已激活"
}

# 安装依赖
install_deps() {
    log_info "检查并安装依赖..."
    cd "$BACKEND_DIR"
    
    # 检查是否需要安装
    if ! pip show fastapi &> /dev/null; then
        log_warning "依赖未安装，正在安装..."
        pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt
        log_success "依赖安装完成"
    else
        log_success "依赖已安装"
    fi
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    # 这里可以添加实际的数据库连接检查
    # 暂时跳过，让应用启动时自己处理
    log_warning "请确保 PostgreSQL 运行在 localhost:5433"
    log_warning "请确保 Redis 运行在 localhost:6380"
}

# 运行数据库初始化
run_migrations() {
    log_info "运行数据库初始化..."
    cd "$BACKEND_DIR"
    
    # 使用新的完整初始化脚本
    if [ -f "init_db.py" ]; then
        log_info "检查数据库表结构..."
        # 非交互式环境，自动回答 yes
        echo "yes" | python init_db.py || log_warning "初始化脚本执行失败"
    elif [ -f "migrate_auth.py" ]; then
        log_warning "使用旧版迁移脚本..."
        python migrate_auth.py || log_warning "迁移脚本执行失败"
    else
        log_warning "未找到数据库初始化脚本，跳过"
    fi
}

# 启动服务
start_server() {
    log_info "启动后端服务 (模式: $MODE)..."
    cd "$BACKEND_DIR"
    
    if [ "$MODE" = "prod" ]; then
        log_info "使用生产模式启动..."
        gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    else
        log_info "使用开发模式启动..."
        log_info "API 文档: http://localhost:8000/docs"
        python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
    fi
}

# 主函数
main() {
    echo "========================================"
    echo "  星灵 AI 伴侣 - 后端启动脚本"
    echo "========================================"
    echo ""
    
    check_python
    check_venv
    activate_venv
    install_deps
    check_database
    run_migrations
    
    echo ""
    log_success "所有检查通过，准备启动服务..."
    echo ""
    
    start_server
}

# 捕获中断信号
trap 'log_error "服务被中断"; exit 1' INT TERM

# 运行主函数
main
