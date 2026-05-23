#!/bin/bash

# 星灵 AI 伴侣 - 一键启动脚本
# 同时启动后端和前端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "1/4 检查环境依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python3，请先安装 Python 3.10+"
        exit 1
    fi
    log_success "Python3 已安装"
    
    # 检查 Flutter
    if ! command -v flutter &> /dev/null; then
        log_error "未找到 Flutter，请先安装 Flutter SDK"
        log_info "安装指南: https://docs.flutter.dev/get-started/install"
        exit 1
    fi
    log_success "Flutter 已安装"
    
    # 检查 Docker（可选）
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        log_success "Docker 已安装，可用于启动数据库"
        HAS_DOCKER=true
    else
        log_warning "未找到 Docker，请确保 PostgreSQL 和 Redis 已手动安装"
        HAS_DOCKER=false
    fi
}

# 启动基础设施
start_infrastructure() {
    log_step "2/4 启动基础设施..."
    
    if [ "$HAS_DOCKER" = true ] && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        log_info "使用 Docker 启动 PostgreSQL 和 Redis..."
        cd "$PROJECT_ROOT"
        docker-compose up -d
        
        # 等待数据库就绪
        log_info "等待数据库就绪..."
        sleep 3
        
        # 检查 PostgreSQL
        if docker-compose ps | grep -q "postgres.*Up"; then
            log_success "PostgreSQL 已启动"
        else
            log_warning "PostgreSQL 启动状态未知"
        fi
        
        # 检查 Redis
        if docker-compose ps | grep -q "redis.*Up"; then
            log_success "Redis 已启动"
        else
            log_warning "Redis 启动状态未知"
        fi
    else
        log_warning "跳过 Docker 启动，请确保 PostgreSQL 和 Redis 已手动运行"
        log_info "  - PostgreSQL: localhost:5433"
        log_info "  - Redis: localhost:6380"
    fi
}

# 启动后端
start_backend() {
    log_step "3/4 启动后端服务..."
    
    log_info "后端服务将在新窗口/标签页中启动..."
    
    # 检测操作系统和终端类型
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v osascript &> /dev/null; then
            # 使用 AppleScript 打开新终端窗口
            osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_ROOT' && ./scripts/start-backend.sh\""
        else
            # 后台启动
            cd "$PROJECT_ROOT" && ./scripts/start-backend.sh &
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd '$PROJECT_ROOT' && ./scripts/start-backend.sh; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd '$PROJECT_ROOT' && ./scripts/start-backend.sh" &
        elif command -v konsole &> /dev/null; then
            konsole -e "cd '$PROJECT_ROOT' && ./scripts/start-backend.sh" &
        else
            # 后台启动
            cd "$PROJECT_ROOT" && ./scripts/start-backend.sh &
        fi
    else
        # Windows (Git Bash)
        cd "$PROJECT_ROOT" && ./scripts/start-backend.sh &
    fi
    
    log_success "后端服务启动中..."
    log_info "API 文档: http://localhost:8000/docs"
    
    # 等待后端启动
    log_info "等待后端服务就绪 (约 5 秒)..."
    sleep 5
}

# 启动前端
start_frontend() {
    log_step "4/4 启动前端应用..."
    
    log_info "前端应用将在当前窗口启动..."
    cd "$PROJECT_ROOT" && ./scripts/start-frontend.sh chrome
}

# 显示使用说明
show_usage() {
    echo ""
    echo "========================================"
    echo "  星灵 AI 伴侣 - 启动完成"
    echo "========================================"
    echo ""
    echo "服务地址:"
    echo "  - 后端 API: http://localhost:8000"
    echo "  - API 文档: http://localhost:8000/docs"
    echo "  - 前端应用: http://localhost:5000 (Chrome)"
    echo ""
    echo "常用命令:"
    echo "  ./scripts/start-backend.sh      # 单独启动后端"
    echo "  ./scripts/start-frontend.sh     # 单独启动前端"
    echo "  docker-compose down             # 停止数据库"
    echo ""
    echo "按 Ctrl+C 停止前端服务"
    echo ""
}

# 清理函数
cleanup() {
    echo ""
    log_warning "正在停止服务..."
    
    # 停止 Docker 容器
    if [ "$HAS_DOCKER" = true ] && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        cd "$PROJECT_ROOT"
        docker-compose down 2>/dev/null || true
    fi
    
    log_success "服务已停止"
    exit 0
}

# 主函数
main() {
    echo "========================================"
    echo "  星灵 AI 伴侣 - 一键启动"
    echo "========================================"
    echo ""
    
    # 设置中断处理
    trap cleanup INT TERM
    
    # 检查脚本是否存在
    if [ ! -f "$SCRIPTS_DIR/start-backend.sh" ]; then
        log_error "未找到后端启动脚本: $SCRIPTS_DIR/start-backend.sh"
        exit 1
    fi
    
    if [ ! -f "$SCRIPTS_DIR/start-frontend.sh" ]; then
        log_error "未找到前端启动脚本: $SCRIPTS_DIR/start-frontend.sh"
        exit 1
    fi
    
    # 给脚本添加执行权限
    chmod +x "$SCRIPTS_DIR/start-backend.sh"
    chmod +x "$SCRIPTS_DIR/start-frontend.sh"
    
    check_dependencies
    start_infrastructure
    start_backend
    show_usage
    start_frontend
}

# 运行主函数
main
