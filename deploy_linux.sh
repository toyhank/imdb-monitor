#!/bin/bash

# IMDB Top 250 监控程序 Linux 部署脚本
# 使用方法: chmod +x deploy_linux.sh && ./deploy_linux.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "检测到root用户，建议使用普通用户运行"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统类型
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统类型"
        exit 1
    fi
    log_info "检测到操作系统: $OS $VER"
}

# 安装系统依赖
install_system_deps() {
    log_step "安装系统依赖..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv git curl
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum update -y
        sudo yum install -y python3 python3-pip git curl
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf update -y
        sudo dnf install -y python3 python3-pip git curl
    else
        log_error "不支持的包管理器，请手动安装 python3, pip, git, curl"
        exit 1
    fi
}

# 检查Python版本
check_python() {
    log_step "检查Python版本..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python版本: $PYTHON_VERSION"
    
    # 检查版本是否 >= 3.7
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 7) else 1)'; then
        log_info "Python版本检查通过"
    else
        log_error "需要Python 3.7或更高版本"
        exit 1
    fi
}

# 创建项目目录和虚拟环境
setup_project() {
    log_step "设置项目环境..."
    
    PROJECT_DIR="$HOME/imdb-monitor"
    
    # 如果目录已存在，询问是否覆盖
    if [[ -d "$PROJECT_DIR" ]]; then
        log_warn "项目目录已存在: $PROJECT_DIR"
        read -p "是否删除并重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            log_info "使用现有目录"
        fi
    fi
    
    # 创建项目目录
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # 创建虚拟环境
    log_info "创建Python虚拟环境..."
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    log_info "项目目录: $PROJECT_DIR"
}

# 复制项目文件
copy_project_files() {
    log_step "复制项目文件..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [[ "$SCRIPT_DIR" != "$PROJECT_DIR" ]]; then
        # 复制Python文件
        find "$SCRIPT_DIR" -name "*.py" -exec cp {} "$PROJECT_DIR/" \;

        # 复制必要文件
        [[ -f "$SCRIPT_DIR/requirements.txt" ]] && cp "$SCRIPT_DIR/requirements.txt" "$PROJECT_DIR/"
        [[ -f "$SCRIPT_DIR/config.env.example" ]] && cp "$SCRIPT_DIR/config.env.example" "$PROJECT_DIR/"
        [[ -f "$SCRIPT_DIR/README.md" ]] && cp "$SCRIPT_DIR/README.md" "$PROJECT_DIR/"

        # 复制目录
        [[ -d "$SCRIPT_DIR/web" ]] && cp -r "$SCRIPT_DIR/web" "$PROJECT_DIR/"
        [[ -d "$SCRIPT_DIR/api" ]] && cp -r "$SCRIPT_DIR/api" "$PROJECT_DIR/"
        [[ -d "$SCRIPT_DIR/deploy" ]] && cp -r "$SCRIPT_DIR/deploy" "$PROJECT_DIR/"
    fi

    # 如果没有config.env，从示例创建
    if [[ ! -f "$PROJECT_DIR/config.env" && -f "$PROJECT_DIR/config.env.example" ]]; then
        cp "$PROJECT_DIR/config.env.example" "$PROJECT_DIR/config.env"
        log_info "已从示例创建config.env文件"
    fi

    log_info "项目文件复制完成"
}

# 安装Python依赖
install_python_deps() {
    log_step "安装Python依赖..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    pip install -r requirements.txt
    
    log_info "Python依赖安装完成"
}

# 配置文件设置
setup_config() {
    log_step "配置文件设置..."
    
    cd "$PROJECT_DIR"
    
    if [[ ! -f config.env ]]; then
        log_error "config.env 文件不存在"
        exit 1
    fi
    
    log_info "请编辑 config.env 文件配置通知设置"
    echo "主要配置项："
    echo "  - WEBHOOK_URL: Webhook通知地址"
    echo "  - EMAIL_USERNAME: 邮箱用户名"
    echo "  - EMAIL_PASSWORD: 邮箱密码"
    echo "  - SCHEDULE_TIME: 执行时间"
    
    read -p "是否现在编辑配置文件? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} config.env
    fi
}

# 创建systemd服务
create_systemd_service() {
    log_step "创建systemd服务..."
    
    SERVICE_FILE="/etc/systemd/system/imdb-monitor.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=IMDB Top 250 Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    sudo systemctl daemon-reload
    
    log_info "systemd服务创建完成"
    log_info "服务文件: $SERVICE_FILE"
}

# 创建cron任务
setup_cron() {
    log_step "设置cron定时任务..."
    
    CRON_SCRIPT="$PROJECT_DIR/run_check.sh"
    
    # 创建执行脚本
    cat > "$CRON_SCRIPT" <<EOF
#!/bin/bash
cd $PROJECT_DIR
source venv/bin/activate
python main.py --once >> logs/cron.log 2>&1
EOF
    
    chmod +x "$CRON_SCRIPT"
    
    # 创建日志目录
    mkdir -p "$PROJECT_DIR/logs"
    
    # 添加cron任务（每天9点执行）
    CRON_JOB="0 9 * * * $CRON_SCRIPT"
    
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
        log_info "cron任务已存在"
    else
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        log_info "cron任务添加完成"
    fi
    
    log_info "cron脚本: $CRON_SCRIPT"
}

# 测试安装
test_installation() {
    log_step "测试安装..."

    cd "$PROJECT_DIR"
    source venv/bin/activate

    log_info "检查Python模块导入..."
    if python -c "import requests, beautifulsoup4, pandas, openpyxl; print('所有依赖模块正常')"; then
        log_info "依赖检查通过"
    else
        log_error "依赖检查失败"
        return 1
    fi

    log_info "执行一次检查..."
    if timeout 60 python main.py --once; then
        log_info "程序运行正常"
    else
        log_warn "程序运行有问题，请检查配置和网络连接"
    fi
}

# 显示部署信息
show_deployment_info() {
    log_step "部署完成！"
    
    echo
    echo "=========================================="
    echo "IMDB Top 250 监控程序部署信息"
    echo "=========================================="
    echo
    echo "项目目录: $PROJECT_DIR"
    echo "虚拟环境: $PROJECT_DIR/venv"
    echo "配置文件: $PROJECT_DIR/config.env"
    echo "日志文件: $PROJECT_DIR/imdb_monitor.log"
    echo
    echo "运行方式："
    echo "1. 手动运行:"
    echo "   cd $PROJECT_DIR"
    echo "   source venv/bin/activate"
    echo "   python main.py --once"
    echo
    echo "2. systemd服务:"
    echo "   sudo systemctl start imdb-monitor"
    echo "   sudo systemctl enable imdb-monitor"
    echo "   sudo systemctl status imdb-monitor"
    echo
    echo "3. cron定时任务:"
    echo "   crontab -l  # 查看任务"
    echo "   tail -f $PROJECT_DIR/logs/cron.log  # 查看日志"
    echo
    echo "配置文件编辑:"
    echo "   nano $PROJECT_DIR/config.env"
    echo
    echo "查看日志:"
    echo "   tail -f $PROJECT_DIR/imdb_monitor.log"
    echo
    echo "=========================================="
}

# 主函数
main() {
    echo "IMDB Top 250 监控程序 Linux 部署脚本"
    echo "======================================"
    
    check_root
    detect_os
    install_system_deps
    check_python
    setup_project
    copy_project_files
    install_python_deps
    setup_config
    
    echo
    echo "选择部署方式："
    echo "1) systemd服务 (推荐)"
    echo "2) cron定时任务"
    echo "3) 两者都设置"
    read -p "请选择 (1-3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            create_systemd_service
            ;;
        2)
            setup_cron
            ;;
        3)
            create_systemd_service
            setup_cron
            ;;
        *)
            log_info "跳过服务设置"
            ;;
    esac
    
    test_installation
    show_deployment_info
}

# 运行主函数
main "$@"
