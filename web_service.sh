#!/bin/bash

# IMDB监控系统 Web服务管理脚本
# 提供多种方式保证Web服务持续运行

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

# 显示帮助信息
show_help() {
    echo "IMDB监控系统 Web服务管理脚本"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  setup-systemd    设置systemd服务"
    echo "  setup-supervisor 设置supervisor服务"
    echo "  setup-screen     设置screen会话"
    echo "  setup-pm2        设置PM2进程管理"
    echo "  start            启动Web服务"
    echo "  stop             停止Web服务"
    echo "  restart          重启Web服务"
    echo "  status           查看服务状态"
    echo "  logs             查看服务日志"
    echo "  install          交互式安装向导"
    echo "  help             显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 install       # 运行安装向导"
    echo "  $0 setup-systemd # 设置systemd服务"
    echo "  $0 start         # 启动Web服务"
    echo "  $0 status        # 查看服务状态"
}

# 检测项目目录和环境
detect_environment() {
    PROJECT_DIR="$(pwd)"
    
    # 检查必要文件
    if [[ ! -f main.py ]]; then
        log_error "未找到main.py文件，请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 检测虚拟环境
    if [[ -d venv ]]; then
        PYTHON_CMD="$PROJECT_DIR/venv/bin/python"
        VENV_ACTIVATE="source $PROJECT_DIR/venv/bin/activate"
    else
        PYTHON_CMD="python3"
        VENV_ACTIVATE=""
    fi
    
    # 检测端口
    WEB_PORT=$(grep "WEB_PORT=" config.env 2>/dev/null | cut -d'=' -f2 || echo "5000")
    
    log_info "项目目录: $PROJECT_DIR"
    log_info "Python命令: $PYTHON_CMD"
    log_info "Web端口: $WEB_PORT"
}

# 方法1: systemd服务
setup_systemd() {
    log_step "设置systemd服务..."
    
    SERVICE_FILE="/etc/systemd/system/imdb-monitor-web.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=IMDB Top 250 Monitor Web Interface
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PYTHON_CMD main.py --web
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StartLimitInterval=60
StartLimitBurst=3
StandardOutput=journal
StandardError=journal

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable imdb-monitor-web
    
    log_success "systemd服务已设置"
    echo "启动服务: sudo systemctl start imdb-monitor-web"
    echo "查看状态: sudo systemctl status imdb-monitor-web"
    echo "查看日志: sudo journalctl -u imdb-monitor-web -f"
}

# 方法2: supervisor服务
setup_supervisor() {
    log_step "设置supervisor服务..."
    
    # 安装supervisor
    if ! command -v supervisord &>/dev/null; then
        log_info "安装supervisor..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get update && sudo apt-get install -y supervisor
        elif command -v yum &>/dev/null; then
            sudo yum install -y supervisor
        else
            log_error "请手动安装supervisor"
            return 1
        fi
    fi
    
    # 创建配置文件
    SUPERVISOR_CONF="/etc/supervisor/conf.d/imdb-monitor-web.conf"
    
    sudo tee "$SUPERVISOR_CONF" > /dev/null <<EOF
[program:imdb-monitor-web]
command=$PYTHON_CMD main.py --web
directory=$PROJECT_DIR
user=$USER
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=$PROJECT_DIR/logs/web_supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="$PROJECT_DIR/venv/bin"
EOF
    
    # 创建日志目录
    mkdir -p "$PROJECT_DIR/logs"
    
    # 重新加载supervisor配置
    sudo supervisorctl reread
    sudo supervisorctl update
    
    log_success "supervisor服务已设置"
    echo "启动服务: sudo supervisorctl start imdb-monitor-web"
    echo "查看状态: sudo supervisorctl status imdb-monitor-web"
    echo "查看日志: tail -f $PROJECT_DIR/logs/web_supervisor.log"
}

# 方法3: screen会话
setup_screen() {
    log_step "设置screen会话..."
    
    # 安装screen
    if ! command -v screen &>/dev/null; then
        log_info "安装screen..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get update && sudo apt-get install -y screen
        elif command -v yum &>/dev/null; then
            sudo yum install -y screen
        else
            log_error "请手动安装screen"
            return 1
        fi
    fi
    
    # 创建启动脚本
    cat > start_web_screen.sh <<EOF
#!/bin/bash
cd "$PROJECT_DIR"
$VENV_ACTIVATE
python main.py --web
EOF
    chmod +x start_web_screen.sh
    
    # 创建管理脚本
    cat > manage_web_screen.sh <<EOF
#!/bin/bash

case "\$1" in
    start)
        if screen -list | grep -q "imdb-web"; then
            echo "Web服务已在运行"
        else
            screen -dmS imdb-web ./start_web_screen.sh
            echo "Web服务已启动"
        fi
        ;;
    stop)
        screen -S imdb-web -X quit 2>/dev/null || echo "Web服务未运行"
        echo "Web服务已停止"
        ;;
    status)
        if screen -list | grep -q "imdb-web"; then
            echo "Web服务正在运行"
        else
            echo "Web服务未运行"
        fi
        ;;
    attach)
        screen -r imdb-web
        ;;
    *)
        echo "用法: \$0 {start|stop|status|attach}"
        ;;
esac
EOF
    chmod +x manage_web_screen.sh
    
    log_success "screen会话已设置"
    echo "启动服务: ./manage_web_screen.sh start"
    echo "查看状态: ./manage_web_screen.sh status"
    echo "连接会话: ./manage_web_screen.sh attach"
}

# 方法4: PM2进程管理
setup_pm2() {
    log_step "设置PM2进程管理..."
    
    # 安装Node.js和PM2
    if ! command -v pm2 &>/dev/null; then
        log_info "安装Node.js和PM2..."
        
        # 安装Node.js
        if ! command -v node &>/dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
        fi
        
        # 安装PM2
        sudo npm install -g pm2
    fi
    
    # 创建PM2配置文件
    cat > ecosystem.config.js <<EOF
module.exports = {
  apps: [{
    name: 'imdb-monitor-web',
    script: '$PYTHON_CMD',
    args: 'main.py --web',
    cwd: '$PROJECT_DIR',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PATH: '$PROJECT_DIR/venv/bin:\$PATH'
    },
    error_file: '$PROJECT_DIR/logs/web_error.log',
    out_file: '$PROJECT_DIR/logs/web_out.log',
    log_file: '$PROJECT_DIR/logs/web_combined.log',
    time: true
  }]
};
EOF
    
    # 创建日志目录
    mkdir -p "$PROJECT_DIR/logs"
    
    log_success "PM2配置已设置"
    echo "启动服务: pm2 start ecosystem.config.js"
    echo "查看状态: pm2 status"
    echo "查看日志: pm2 logs imdb-monitor-web"
    echo "设置开机自启: pm2 startup && pm2 save"
}

# 启动Web服务
start_web() {
    log_step "启动Web服务..."
    
    if systemctl is-active imdb-monitor-web &>/dev/null; then
        sudo systemctl start imdb-monitor-web
        log_success "systemd服务已启动"
    elif command -v supervisorctl &>/dev/null && sudo supervisorctl status imdb-monitor-web &>/dev/null; then
        sudo supervisorctl start imdb-monitor-web
        log_success "supervisor服务已启动"
    elif [[ -f manage_web_screen.sh ]]; then
        ./manage_web_screen.sh start
        log_success "screen会话已启动"
    elif command -v pm2 &>/dev/null && [[ -f ecosystem.config.js ]]; then
        pm2 start ecosystem.config.js
        log_success "PM2服务已启动"
    else
        log_warn "未找到配置的服务管理器，使用后台运行..."
        nohup $PYTHON_CMD main.py --web > logs/web.log 2>&1 &
        echo $! > web.pid
        log_success "Web服务已在后台启动"
    fi
    
    echo "Web界面: http://localhost:$WEB_PORT"
}

# 停止Web服务
stop_web() {
    log_step "停止Web服务..."
    
    # 尝试各种方式停止
    if systemctl is-active imdb-monitor-web &>/dev/null; then
        sudo systemctl stop imdb-monitor-web
        log_info "systemd服务已停止"
    fi
    
    if command -v supervisorctl &>/dev/null; then
        sudo supervisorctl stop imdb-monitor-web 2>/dev/null || true
        log_info "supervisor服务已停止"
    fi
    
    if [[ -f manage_web_screen.sh ]]; then
        ./manage_web_screen.sh stop
        log_info "screen会话已停止"
    fi
    
    if command -v pm2 &>/dev/null; then
        pm2 stop imdb-monitor-web 2>/dev/null || true
        log_info "PM2服务已停止"
    fi
    
    # 强制杀死进程
    pkill -f "python.*main.py.*--web" 2>/dev/null || true
    
    log_success "Web服务已停止"
}

# 查看服务状态
show_status() {
    log_step "检查Web服务状态..."
    
    echo "=== systemd服务 ==="
    if systemctl is-active imdb-monitor-web &>/dev/null; then
        sudo systemctl status imdb-monitor-web --no-pager
    else
        echo "systemd服务未运行"
    fi
    
    echo
    echo "=== supervisor服务 ==="
    if command -v supervisorctl &>/dev/null; then
        sudo supervisorctl status imdb-monitor-web 2>/dev/null || echo "supervisor服务未配置"
    else
        echo "supervisor未安装"
    fi
    
    echo
    echo "=== screen会话 ==="
    if command -v screen &>/dev/null; then
        screen -list | grep imdb-web || echo "screen会话未运行"
    else
        echo "screen未安装"
    fi
    
    echo
    echo "=== PM2服务 ==="
    if command -v pm2 &>/dev/null; then
        pm2 list | grep imdb-monitor-web || echo "PM2服务未运行"
    else
        echo "PM2未安装"
    fi
    
    echo
    echo "=== 端口检查 ==="
    if netstat -tlnp 2>/dev/null | grep ":$WEB_PORT "; then
        log_success "Web服务正在监听端口 $WEB_PORT"
    else
        log_warn "端口 $WEB_PORT 未被监听"
    fi
}

# 查看日志
show_logs() {
    log_step "查看Web服务日志..."
    
    echo "选择日志类型："
    echo "1) systemd日志"
    echo "2) supervisor日志"
    echo "3) 应用日志"
    echo "4) 所有日志"
    
    read -p "请选择 (1-4): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            sudo journalctl -u imdb-monitor-web -f
            ;;
        2)
            tail -f "$PROJECT_DIR/logs/web_supervisor.log" 2>/dev/null || echo "supervisor日志不存在"
            ;;
        3)
            tail -f "$PROJECT_DIR/logs/web.log" 2>/dev/null || echo "应用日志不存在"
            ;;
        4)
            echo "=== systemd日志 ==="
            sudo journalctl -u imdb-monitor-web -n 20 --no-pager
            echo
            echo "=== supervisor日志 ==="
            tail -20 "$PROJECT_DIR/logs/web_supervisor.log" 2>/dev/null || echo "supervisor日志不存在"
            echo
            echo "=== 应用日志 ==="
            tail -20 "$PROJECT_DIR/logs/web.log" 2>/dev/null || echo "应用日志不存在"
            ;;
        *)
            log_error "无效选择"
            ;;
    esac
}

# 交互式安装向导
install_wizard() {
    log_step "Web服务安装向导"
    
    echo
    echo "选择Web服务管理方式："
    echo "1) systemd (推荐，适合生产环境)"
    echo "2) supervisor (适合多服务管理)"
    echo "3) screen (适合开发环境)"
    echo "4) PM2 (适合Node.js环境)"
    echo
    read -p "请选择 (1-4): " -n 1 -r
    echo
    
    case $REPLY in
        1) setup_systemd ;;
        2) setup_supervisor ;;
        3) setup_screen ;;
        4) setup_pm2 ;;
        *) log_error "无效选择"; exit 1 ;;
    esac
    
    echo
    read -p "是否现在启动Web服务? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_web
    fi
}

# 主函数
main() {
    detect_environment
    
    case "${1:-install}" in
        setup-systemd)
            setup_systemd
            ;;
        setup-supervisor)
            setup_supervisor
            ;;
        setup-screen)
            setup_screen
            ;;
        setup-pm2)
            setup_pm2
            ;;
        start)
            start_web
            ;;
        stop)
            stop_web
            ;;
        restart)
            stop_web
            sleep 2
            start_web
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        install)
            install_wizard
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
