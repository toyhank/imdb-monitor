#!/bin/bash

# IMDB Top 250 监控程序 Docker 部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查Docker是否安装
check_docker() {
    log_step "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        echo "安装命令："
        echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
        echo "  CentOS/RHEL: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_warn "docker-compose未安装，尝试安装..."
        
        # 尝试安装docker-compose
        if command -v pip3 &> /dev/null; then
            pip3 install docker-compose
        else
            log_error "请手动安装docker-compose"
            exit 1
        fi
    fi
    
    # 检查Docker服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        echo "启动命令: sudo systemctl start docker"
        exit 1
    fi
    
    log_info "Docker环境检查通过"
}

# 创建项目目录结构
setup_directories() {
    log_step "创建项目目录结构..."
    
    mkdir -p data logs
    
    # 设置权限
    chmod 755 data logs
    
    log_info "目录结构创建完成"
}

# 配置环境变量
setup_env() {
    log_step "配置环境变量..."
    
    if [[ ! -f .env ]]; then
        log_info "创建.env文件..."
        cat > .env <<EOF
# IMDB监控程序环境变量
# 复制并修改这些值

# Webhook通知
WEBHOOK_URL=https://your-webhook-url.com/notify
NOTIFICATION_TYPE=webhook

# 邮件通知（如果使用邮件）
# NOTIFICATION_TYPE=email
# EMAIL_USERNAME=your-email@gmail.com
# EMAIL_PASSWORD=your-app-password
# EMAIL_TO=recipient@example.com

# 调度设置
SCHEDULE_TIME=09:00

# 日志级别
LOG_LEVEL=INFO
EOF
        log_warn "请编辑.env文件配置通知设置"
    else
        log_info ".env文件已存在"
    fi
    
    read -p "是否现在编辑.env文件? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
}

# 构建Docker镜像
build_image() {
    log_step "构建Docker镜像..."
    
    docker build -t imdb-monitor:latest .
    
    log_info "Docker镜像构建完成"
}

# 运行容器
run_container() {
    log_step "启动容器..."
    
    # 停止现有容器
    if docker ps -a | grep -q imdb-monitor; then
        log_info "停止现有容器..."
        docker-compose down
    fi
    
    # 启动新容器
    docker-compose up -d
    
    log_info "容器启动完成"
}

# 测试部署
test_deployment() {
    log_step "测试部署..."
    
    # 等待容器启动
    sleep 5
    
    # 检查容器状态
    if docker ps | grep -q imdb-monitor; then
        log_info "容器运行正常"
    else
        log_error "容器启动失败"
        docker-compose logs
        exit 1
    fi
    
    # 运行测试
    log_info "运行功能测试..."
    docker-compose exec imdb-monitor python demo.py
    
    # 执行一次检查
    log_info "执行一次检查..."
    docker-compose exec imdb-monitor python main.py --once
}

# 显示管理命令
show_management_commands() {
    log_step "部署完成！"
    
    echo
    echo "=========================================="
    echo "Docker 部署管理命令"
    echo "=========================================="
    echo
    echo "容器管理："
    echo "  启动: docker-compose up -d"
    echo "  停止: docker-compose down"
    echo "  重启: docker-compose restart"
    echo "  状态: docker-compose ps"
    echo
    echo "日志查看："
    echo "  实时日志: docker-compose logs -f"
    echo "  程序日志: docker-compose exec imdb-monitor tail -f /app/logs/imdb_monitor.log"
    echo
    echo "进入容器："
    echo "  交互模式: docker-compose exec imdb-monitor bash"
    echo "  执行命令: docker-compose exec imdb-monitor python main.py --once"
    echo
    echo "数据管理："
    echo "  数据目录: ./data"
    echo "  日志目录: ./logs"
    echo "  配置文件: ./config.env"
    echo
    echo "更新程序："
    echo "  1. 更新代码文件"
    echo "  2. docker-compose down"
    echo "  3. docker build -t imdb-monitor:latest ."
    echo "  4. docker-compose up -d"
    echo
    echo "备份数据："
    echo "  tar -czf backup_\$(date +%Y%m%d).tar.gz data/ logs/ config.env .env"
    echo
    echo "=========================================="
}

# 安装Docker（可选）
install_docker() {
    log_step "安装Docker..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        log_error "不支持的系统，请手动安装Docker"
        exit 1
    fi
    
    log_info "Docker安装完成，请重新登录或运行 'newgrp docker'"
}

# 主函数
main() {
    echo "IMDB Top 250 监控程序 Docker 部署脚本"
    echo "====================================="
    
    # 检查是否需要安装Docker
    if ! command -v docker &> /dev/null; then
        read -p "Docker未安装，是否现在安装? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_docker
            log_warn "请重新登录后再次运行此脚本"
            exit 0
        else
            log_error "需要Docker环境"
            exit 1
        fi
    fi
    
    check_docker
    setup_directories
    setup_env
    build_image
    run_container
    test_deployment
    show_management_commands
}

# 运行主函数
main "$@"
