#!/bin/bash

# IMDB Top 250 监控系统快速部署脚本
# 支持多种部署方式：Docker、虚拟环境、系统服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
log_success() { echo -e "${PURPLE}[SUCCESS]${NC} $1"; }

# 显示横幅
show_banner() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "    IMDB Top 250 监控系统快速部署脚本"
    echo "    (使用已下载的项目文件)"
    echo "=================================================="
    echo -e "${NC}"
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "此脚本仅支持Linux系统"
        exit 1
    fi
    
    # 检查网络连接
    if ! curl -s --connect-timeout 5 https://www.imdb.com > /dev/null; then
        log_warn "无法连接到IMDB，请检查网络连接"
    fi
    
    log_info "系统检查完成"
}

# 选择部署方式
choose_deployment_method() {
    # 首先检查项目文件
    check_project_files

    echo
    echo "请选择部署方式："
    echo "1) Docker部署 (推荐)"
    echo "2) Python虚拟环境部署"
    echo "3) 系统级安装"
    echo
    read -p "请输入选择 (1-3): " -n 1 -r
    echo

    case $REPLY in
        1) deploy_with_docker ;;
        2) deploy_with_venv ;;
        3) deploy_system_wide ;;
        *) log_error "无效选择"; exit 1 ;;
    esac
}

# Docker部署
deploy_with_docker() {
    log_step "开始Docker部署..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_info "安装Docker..."
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
        log_warn "请重新登录以使Docker权限生效"
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_info "安装Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    # 使用当前目录作为项目目录
    PROJECT_DIR="$(pwd)"
    log_info "使用当前目录: $PROJECT_DIR"

    # 创建配置文件
    if [[ ! -f config.env ]]; then
        if [[ -f config.env.example ]]; then
            cp config.env.example config.env
            log_info "已从示例创建 config.env 文件，请编辑配置通知设置"
        else
            log_error "未找到 config.env.example 文件"
            return 1
        fi
    fi

    # 创建数据目录
    mkdir -p data logs backups

    # 启动服务
    log_info "启动Docker服务..."
    docker-compose up -d

    log_success "Docker部署完成！"
    echo "Web界面: http://localhost:5000"
    echo "查看日志: docker-compose logs -f"
    echo "停止服务: docker-compose down"
}

# 虚拟环境部署
deploy_with_venv() {
    log_step "开始虚拟环境部署..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_info "安装Python3..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip
        else
            log_error "请手动安装Python3"
            exit 1
        fi
    fi

    # 使用当前目录作为项目目录
    PROJECT_DIR="$(pwd)"
    log_info "使用当前目录: $PROJECT_DIR"

    # 检查必要文件
    if [[ ! -f main.py ]]; then
        log_error "未找到 main.py 文件，请确保在项目根目录运行此脚本"
        exit 1
    fi

    # 创建虚拟环境
    log_info "创建Python虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate

    # 安装依赖
    log_info "安装Python依赖..."
    pip install --upgrade pip
    if [[ -f requirements.txt ]]; then
        pip install -r requirements.txt
    else
        log_error "未找到 requirements.txt 文件"
        exit 1
    fi

    # 创建配置文件
    if [[ ! -f config.env ]]; then
        if [[ -f config.env.example ]]; then
            cp config.env.example config.env
            log_info "已从示例创建 config.env 文件，请编辑配置通知设置"
        else
            log_error "未找到 config.env.example 文件"
            exit 1
        fi
    fi

    # 创建启动脚本
    create_startup_scripts

    # 设置系统服务
    setup_systemd_service

    log_success "虚拟环境部署完成！"
    echo "项目目录: $PROJECT_DIR"
    echo "启动命令: cd $PROJECT_DIR && source venv/bin/activate && python main.py"
    echo "Web界面: python main.py --web"
}

# 系统级安装
deploy_system_wide() {
    log_step "开始系统级安装..."

    # 安装系统依赖
    log_info "安装系统依赖..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip git curl sqlite3
    elif command -v yum &> /dev/null; then
        sudo yum update -y
        sudo yum install -y python3 python3-pip git curl sqlite3
    else
        log_error "不支持的包管理器"
        exit 1
    fi

    # 创建系统目录并复制文件
    PROJECT_DIR="/opt/imdb-monitor"
    sudo mkdir -p "$PROJECT_DIR"

    # 复制当前目录的文件到系统目录
    log_info "复制项目文件到系统目录..."
    sudo cp -r . "$PROJECT_DIR/"
    sudo chown -R $USER:$USER "$PROJECT_DIR"
    cd "$PROJECT_DIR"

    # 安装Python依赖
    log_info "安装Python依赖..."
    if [[ -f requirements.txt ]]; then
        sudo pip3 install -r requirements.txt
    else
        log_error "未找到 requirements.txt 文件"
        exit 1
    fi

    # 创建配置文件
    if [[ ! -f config.env ]]; then
        if [[ -f config.env.example ]]; then
            cp config.env.example config.env
            log_info "已从示例创建 config.env 文件，请编辑配置通知设置"
        else
            log_error "未找到 config.env.example 文件"
            exit 1
        fi
    fi

    # 设置系统服务
    setup_systemd_service

    log_success "系统级安装完成！"
    echo "项目目录: $PROJECT_DIR"
    echo "启动服务: sudo systemctl start imdb-monitor"
}

# 检查项目文件
check_project_files() {
    log_step "检查项目文件..."

    PROJECT_DIR="$(pwd)"
    log_info "当前目录: $PROJECT_DIR"

    # 检查必要文件
    local missing_files=()

    [[ ! -f main.py ]] && missing_files+=("main.py")
    [[ ! -f requirements.txt ]] && missing_files+=("requirements.txt")
    [[ ! -f config.env.example ]] && missing_files+=("config.env.example")

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "缺少必要文件: ${missing_files[*]}"
        log_error "请确保在项目根目录运行此脚本"
        exit 1
    fi

    log_info "项目文件检查通过"
}

# 创建启动脚本
create_startup_scripts() {
    log_info "创建启动脚本..."
    
    # 创建启动脚本
    cat > start.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py "$@"
EOF
    
    # 创建Web启动脚本
    cat > start_web.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py --web
EOF
    
    # 创建一次性执行脚本
    cat > run_once.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py --once
EOF
    
    chmod +x *.sh
}

# 设置systemd服务
setup_systemd_service() {
    log_info "设置systemd服务..."

    # 监控服务
    MONITOR_SERVICE_FILE="/etc/systemd/system/imdb-monitor.service"
    sudo tee "$MONITOR_SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=IMDB Top 250 Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Web服务
    WEB_SERVICE_FILE="/etc/systemd/system/imdbmonitor--web.service"
    sudo tee "$WEB_SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=IMDB Top 250 Monitor Web Interface
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/python main.py --web
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    log_info "systemd服务已创建 (监控服务 + Web服务)"

    # 询问是否启用Web服务
    echo
    read -p "是否启用Web服务自动启动? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl enable imdb-monitor-web
        sudo systemctl start imdb-monitor-web
        log_info "Web服务已启用并启动"
        echo "Web界面: http://localhost:5000"
    else
        log_info "Web服务已创建但未启用，可手动启动: sudo systemctl start imdb-monitor-web"
    fi
}

# 显示部署后信息
show_post_deployment_info() {
    echo
    log_success "部署完成！"
    echo
    echo "=========================================="
    echo "部署信息："
    echo "项目目录: $(pwd)"
    echo "配置文件: $(pwd)/config.env"
    echo "日志文件: $(pwd)/imdb_monitor.log"
    echo
    echo "下一步操作："
    echo "1. 编辑配置文件:"
    echo "   nano config.env"
    echo
    echo "2. 测试运行:"
    if [[ -d venv ]]; then
        echo "   source venv/bin/activate"
        echo "   python main.py --once"
    else
        echo "   python3 main.py --once"
    fi
    echo
    echo "3. Web服务管理:"
    echo "   ./web_service.sh install    # 设置Web服务持久运行"
    echo "   ./web_service.sh start      # 启动Web服务"
    echo "   ./web_service.sh status     # 查看Web服务状态"
    echo "   ./web_service.sh logs       # 查看Web服务日志"
    echo
    echo "4. 系统服务管理:"
    echo "   sudo systemctl start imdb-monitor      # 启动监控服务"
    echo "   sudo systemctl start imdb-monitor-web  # 启动Web服务"
    echo "   sudo systemctl status imdb-monitor     # 查看监控服务状态"
    echo
    echo "5. Web服务自动检查 (可选):"
    echo "   # 添加到crontab，每5分钟检查一次"
    echo "   */5 * * * * $(pwd)/check_web_service.sh --cron"
    echo
    echo "Web界面访问: http://localhost:5000"
    echo "更多信息请查看: LINUX_DEPLOYMENT_GUIDE.md"
    echo "=========================================="
}

# 主函数
main() {
    show_banner
    check_requirements
    choose_deployment_method
    show_post_deployment_info
}

# 运行主函数
main "$@"
