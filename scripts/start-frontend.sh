#!/bin/bash

# 星灵 AI 伴侣 - 前端启动脚本
# 用法: ./start-frontend.sh [chrome|edge|device_id]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/flutter_app"

# 目标设备
DEVICE="${1:-chrome}"

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

# 检查 Flutter
check_flutter() {
    log_info "检查 Flutter 环境..."
    if ! command -v flutter &> /dev/null; then
        log_error "未找到 Flutter，请先安装 Flutter SDK"
        log_info "安装指南: https://docs.flutter.dev/get-started/install"
        exit 1
    fi
    
    FLUTTER_VERSION=$(flutter --version | head -1)
    log_success "Flutter: $FLUTTER_VERSION"
}

# 检查设备
check_device() {
    log_info "检查可用设备..."
    
    # 获取设备列表
    DEVICES=$(flutter devices --machine 2>/dev/null | grep -o '"name":[^,]*' | head -5)
    
    if [ -z "$DEVICES" ]; then
        log_warning "未找到可用设备"
        log_info "可用的启动方式:"
        log_info "  - chrome: 在 Chrome 浏览器中运行"
        log_info "  - edge: 在 Edge 浏览器中运行"
        log_info "  - 先连接手机或启动模拟器"
        
        # 检查 Chrome
        if command -v google-chrome &> /dev/null || command -v chromium &> /dev/null || [ -d "/Applications/Google Chrome.app" ]; then
            log_success "检测到 Chrome 浏览器，可以使用 chrome 模式"
        fi
    else
        log_success "可用设备:"
        echo "$DEVICES" | sed 's/"name"://g' | sed 's/"//g' | sed 's/^/  - /'
    fi
}

# 安装依赖
install_deps() {
    log_info "安装 Flutter 依赖..."
    cd "$FRONTEND_DIR"
    
    # 检查 pubspec.yaml 是否存在
    if [ ! -f "pubspec.yaml" ]; then
        log_error "未找到 pubspec.yaml，请确保在正确的目录"
        exit 1
    fi
    
    # 安装依赖
    flutter pub get
    
    log_success "依赖安装完成"
}

# 检查后端是否运行
check_backend() {
    log_info "检查后端服务..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "后端服务运行正常"
    else
        log_warning "后端服务未启动或无法访问"
        log_info "请先运行: ./scripts/start-backend.sh"
        log_info "或者检查后端是否运行在 http://localhost:8000"
    fi
}

# 启动应用
start_app() {
    log_info "启动 Flutter 应用 (设备: $DEVICE)..."
    cd "$FRONTEND_DIR"
    
    case "$DEVICE" in
        chrome)
            log_info "在 Chrome 浏览器中启动..."
            flutter run -d chrome --web-port 5000
            ;;
        edge)
            log_info "在 Edge 浏览器中启动..."
            flutter run -d edge --web-port 5000
            ;;
        *)
            # 尝试作为设备 ID 使用
            log_info "尝试在设备 '$DEVICE' 上启动..."
            flutter run -d "$DEVICE"
            ;;
    esac
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  chrome       在 Chrome 浏览器中运行 (默认)"
    echo "  edge         在 Edge 浏览器中运行"
    echo "  device_id    在指定设备上运行"
    echo "  --help       显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0                    # 在 Chrome 中运行"
    echo "  $0 chrome             # 在 Chrome 中运行"
    echo "  $0 edge               # 在 Edge 中运行"
    echo "  $0 emulator-5554      # 在 Android 模拟器上运行"
    echo ""
    echo "提示:"
    echo "  使用 'flutter devices' 查看可用设备列表"
}

# 主函数
main() {
    # 处理帮助
    if [ "$DEVICE" = "--help" ] || [ "$DEVICE" = "-h" ]; then
        show_help
        exit 0
    fi
    
    echo "========================================"
    echo "  星灵 AI 伴侣 - 前端启动脚本"
    echo "========================================"
    echo ""
    
    check_flutter
    check_device
    install_deps
    check_backend
    
    echo ""
    log_success "准备启动应用..."
    echo ""
    
    start_app
}

# 捕获中断信号
trap 'log_error "应用被中断"; exit 1' INT TERM

# 运行主函数
main
