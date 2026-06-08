#!/bin/bash

# IMDB Top 250 监控系统 - Linux自动部署脚本
# 使用方法: chmod +x deploy.sh && ./deploy.sh

set -e  # 遇到错误立即退出

echo "🚀 IMDB Top 250 监控系统 - Linux部署脚本"
echo "================================================"

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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统
check_system() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_success "检测到Linux系统"
    else
        log_error "此脚本仅支持Linux系统"
        exit 1
    fi
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python3已安装: $PYTHON_VERSION"
    else
        log_error "Python3未安装，请先安装Python3"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        log_success "pip3已安装"
    else
        log_error "pip3未安装，请先安装pip3"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    if command -v apt &> /dev/null; then
        # Ubuntu/Debian
        log_info "检测到apt包管理器，安装Ubuntu/Debian依赖..."
        sudo apt update
        sudo apt install -y python3-venv python3-dev build-essential \
                           libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        log_info "检测到yum包管理器，安装CentOS/RHEL依赖..."
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y python3-devel libxml2-devel libxslt-devel \
                           zlib-devel libjpeg-devel
    elif command -v dnf &> /dev/null; then
        # Fedora/CentOS 8+
        log_info "检测到dnf包管理器，安装Fedora依赖..."
        sudo dnf groupinstall -y "Development Tools"
        sudo dnf install -y python3-devel libxml2-devel libxslt-devel \
                           zlib-devel libjpeg-devel
    else
        log_warning "未检测到支持的包管理器，请手动安装编译依赖"
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "创建Python虚拟环境..."
    
    if [ -d "venv" ]; then
        log_warning "虚拟环境已存在，跳过创建"
    else
        python3 -m venv venv
        log_success "虚拟环境创建成功"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    log_success "虚拟环境已激活"
    
    # 升级pip
    pip install --upgrade pip
}

# 检查项目文件
check_project_files() {
    log_info "检查项目文件..."
    
    REQUIRED_FILES=(
        "main.py"
        "config.py"
        "scraper.py"
        "database.py"
        "change_detector.py"
        "notifier.py"
    )
    
    MISSING_FILES=()
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            log_success "✅ $file 存在"
        else
            log_error "❌ $file 缺失"
            MISSING_FILES+=("$file")
        fi
    done
    
    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        log_error "缺失必要文件，请确保所有项目文件都在当前目录"
        exit 1
    fi
}

# 创建requirements.txt（如果不存在）
create_requirements() {
    if [ ! -f "requirements.txt" ]; then
        log_warning "requirements.txt不存在，创建默认版本..."
        cat > requirements.txt << EOF
requests>=2.31.0
beautifulsoup4>=4.12.0
schedule>=1.2.0
python-dotenv>=1.0.0
lxml>=4.9.0
Pillow>=10.0.0
EOF
        log_success "requirements.txt创建成功"
    else
        log_success "requirements.txt已存在"
    fi
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    # 确保虚拟环境已激活
    source venv/bin/activate
    
    # 尝试使用国内镜像源加速
    if pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/; then
        log_success "依赖安装成功（使用清华镜像源）"
    elif pip install -r requirements.txt; then
        log_success "依赖安装成功（使用默认源）"
    else
        log_error "依赖安装失败"
        exit 1
    fi
}

# 创建配置文件
create_config() {
    if [ ! -f "config.env" ]; then
        log_info "创建配置文件..."
        cat > config.env << EOF
# 企业微信配置
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE
WEBHOOK_TYPE=wework
NOTIFICATION_TYPE=webhook

# 图片功能
ENABLE_MOVIE_IMAGES=true

# 数据库配置
DATABASE_PATH=imdb_top250.db

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=imdb_monitor.log

# 调度配置
SCHEDULE_TIME=09:00

# 用户代理
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
EOF
        log_success "配置文件创建成功"
        log_warning "请编辑 config.env 文件，设置你的企业微信Webhook URL"
    else
        log_success "配置文件已存在"
    fi
}

# 设置权限
set_permissions() {
    log_info "设置文件权限..."
    
    chmod +x main.py
    chmod 600 config.env  # 配置文件设为只有所有者可读写
    
    log_success "权限设置完成"
}

# 测试运行
test_run() {
    log_info "测试程序运行..."
    
    source venv/bin/activate
    
    if python main.py --help > /dev/null 2>&1; then
        log_success "程序可以正常运行"
    else
        log_error "程序运行测试失败"
        exit 1
    fi
}

# 创建systemd服务
create_service() {
    read -p "是否创建systemd服务以便开机自启动？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "创建systemd服务..."
        
        SERVICE_FILE="/etc/systemd/system/imdb-monitor.service"
        WORK_DIR=$(pwd)
        USER=$(whoami)
        
        sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=IMDB Top 250 Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
ExecStart=$WORK_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable imdb-monitor
        
        log_success "systemd服务创建成功"
        log_info "使用以下命令管理服务："
        echo "  启动: sudo systemctl start imdb-monitor"
        echo "  停止: sudo systemctl stop imdb-monitor"
        echo "  状态: sudo systemctl status imdb-monitor"
        echo "  日志: sudo journalctl -u imdb-monitor -f"
    fi
}

# 显示部署完成信息
show_completion() {
    log_success "🎉 部署完成！"
    echo
    echo "📁 项目目录: $(pwd)"
    echo "🐍 Python环境: $(pwd)/venv"
    echo "⚙️  配置文件: $(pwd)/config.env"
    echo "📊 数据库: $(pwd)/imdb_top250.db"
    echo "📝 日志文件: $(pwd)/imdb_monitor.log"
    echo
    echo "🚀 快速开始："
    echo "  1. 编辑配置文件: nano config.env"
    echo "  2. 设置企业微信Webhook URL"
    echo "  3. 测试运行: source venv/bin/activate && python main.py --once"
    echo "  4. 后台运行: nohup python main.py > output.log 2>&1 &"
    echo
    echo "📖 更多信息请查看: LINUX_DEPLOYMENT.md"
}

# 主函数
main() {
    check_system
    install_system_deps
    check_project_files
    create_requirements
    create_venv
    install_python_deps
    create_config
    set_permissions
    test_run
    create_service
    show_completion
}

# 运行主函数
main "$@"
