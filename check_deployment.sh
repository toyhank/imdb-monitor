#!/bin/bash

# IMDB监控系统部署检查脚本
# 用于验证部署是否成功

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_check() { echo -e "${BLUE}[CHECK]${NC} $1"; }

# 检查计数器
TOTAL_CHECKS=0
PASSED_CHECKS=0

# 执行检查
run_check() {
    local check_name="$1"
    local check_command="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    log_check "$check_name"
    
    if eval "$check_command" &>/dev/null; then
        echo "  ✅ 通过"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo "  ❌ 失败"
        return 1
    fi
}

# 显示横幅
echo -e "${BLUE}"
echo "=================================================="
echo "    IMDB监控系统部署检查"
echo "=================================================="
echo -e "${NC}"

# 检查系统环境
echo "🔍 系统环境检查"
echo "----------------------------------------"

run_check "操作系统类型" '[[ "$OSTYPE" == "linux-gnu"* ]]'
run_check "Python3可用性" 'command -v python3'
run_check "Python版本 (>=3.7)" 'python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"'
run_check "pip可用性" 'command -v pip3 || command -v pip'
run_check "curl可用性" 'command -v curl'
run_check "网络连接" 'curl -s --connect-timeout 5 https://www.imdb.com'

# 检查项目文件
echo
echo "📁 项目文件检查"
echo "----------------------------------------"

PROJECT_DIRS=(
    "$HOME/imdb-monitor"
    "/opt/imdb-monitor"
    "$(pwd)"
)

PROJECT_DIR=""
for dir in "${PROJECT_DIRS[@]}"; do
    if [[ -d "$dir" && -f "$dir/main.py" ]]; then
        PROJECT_DIR="$dir"
        break
    fi
done

if [[ -n "$PROJECT_DIR" ]]; then
    log_info "找到项目目录: $PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    run_check "main.py存在" '[[ -f main.py ]]'
    run_check "requirements.txt存在" '[[ -f requirements.txt ]]'
    run_check "config.env存在" '[[ -f config.env ]]'
    run_check "数据库目录可写" '[[ -w . ]]'
    
    # 检查虚拟环境
    if [[ -d venv ]]; then
        run_check "虚拟环境存在" '[[ -d venv ]]'
        run_check "虚拟环境可激活" 'source venv/bin/activate && python --version'
    fi
else
    log_error "未找到项目目录"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 4))
fi

# 检查Python依赖
echo
echo "🐍 Python依赖检查"
echo "----------------------------------------"

if [[ -n "$PROJECT_DIR" ]]; then
    cd "$PROJECT_DIR"
    
    # 激活虚拟环境（如果存在）
    if [[ -d venv ]]; then
        source venv/bin/activate
    fi
    
    run_check "requests模块" 'python3 -c "import requests"'
    run_check "beautifulsoup4模块" 'python3 -c "import bs4"'
    run_check "pandas模块" 'python3 -c "import pandas"'
    run_check "openpyxl模块" 'python3 -c "import openpyxl"'
    run_check "schedule模块" 'python3 -c "import schedule"'
    run_check "flask模块" 'python3 -c "import flask"'
fi

# 检查配置文件
echo
echo "⚙️ 配置文件检查"
echo "----------------------------------------"

if [[ -n "$PROJECT_DIR" && -f "$PROJECT_DIR/config.env" ]]; then
    cd "$PROJECT_DIR"
    
    run_check "WEBHOOK_URL配置" 'grep -q "WEBHOOK_URL=" config.env && ! grep -q "YOUR_KEY_HERE" config.env'
    run_check "EMAIL配置" 'grep -q "EMAIL_USERNAME=" config.env && ! grep -q "your-email@gmail.com" config.env'
    run_check "SCHEDULE_TIME配置" 'grep -q "SCHEDULE_TIME=" config.env'
    run_check "通知类型配置" 'grep -q "NOTIFICATION_TYPE=" config.env'
fi

# 检查服务状态
echo
echo "🔄 服务状态检查"
echo "----------------------------------------"

run_check "systemd服务文件" '[[ -f /etc/systemd/system/imdb-monitor.service ]]'

if [[ -f /etc/systemd/system/imdb-monitor.service ]]; then
    run_check "systemd服务状态" 'systemctl is-active imdb-monitor'
    run_check "systemd服务启用" 'systemctl is-enabled imdb-monitor'
fi

# 检查Docker部署
echo
echo "🐳 Docker部署检查"
echo "----------------------------------------"

if command -v docker &>/dev/null; then
    run_check "Docker可用性" 'docker --version'
    run_check "Docker服务运行" 'docker info'
    
    if command -v docker-compose &>/dev/null; then
        run_check "Docker Compose可用性" 'docker-compose --version'
        
        if [[ -f docker-compose.yml ]]; then
            run_check "Docker Compose配置" 'docker-compose config'
            run_check "Docker容器运行" 'docker-compose ps | grep -q "Up"'
        fi
    fi
else
    log_warn "Docker未安装，跳过Docker检查"
fi

# 检查网络连接
echo
echo "🌐 网络连接检查"
echo "----------------------------------------"

run_check "IMDB网站连接" 'curl -s --connect-timeout 10 https://www.imdb.com/chart/top/ | grep -q "Top 250"'
run_check "TMDB API连接" 'curl -s --connect-timeout 10 https://api.themoviedb.org/3/configuration'

# 检查端口占用
echo
echo "🔌 端口检查"
echo "----------------------------------------"

run_check "端口5000可用" '! netstat -tlnp 2>/dev/null | grep -q ":5000 "'

# 功能测试
echo
echo "🧪 功能测试"
echo "----------------------------------------"

if [[ -n "$PROJECT_DIR" ]]; then
    cd "$PROJECT_DIR"
    
    # 激活虚拟环境（如果存在）
    if [[ -d venv ]]; then
        source venv/bin/activate
    fi
    
    run_check "程序导入测试" 'python3 -c "import main; print(\"导入成功\")"'
    
    # 如果配置正确，尝试运行测试
    if grep -q "WEBHOOK_URL=" config.env && ! grep -q "YOUR_KEY_HERE" config.env; then
        run_check "程序运行测试" 'timeout 30 python3 main.py --once'
    else
        log_warn "配置未完成，跳过运行测试"
    fi
fi

# 显示结果
echo
echo "📊 检查结果"
echo "=========================================="
echo "总检查项: $TOTAL_CHECKS"
echo "通过检查: $PASSED_CHECKS"
echo "失败检查: $((TOTAL_CHECKS - PASSED_CHECKS))"

if [[ $PASSED_CHECKS -eq $TOTAL_CHECKS ]]; then
    echo -e "${GREEN}🎉 所有检查通过！部署成功！${NC}"
    exit 0
elif [[ $PASSED_CHECKS -gt $((TOTAL_CHECKS * 3 / 4)) ]]; then
    echo -e "${YELLOW}⚠️  大部分检查通过，部署基本成功${NC}"
    echo "请检查失败的项目并进行修复"
    exit 0
else
    echo -e "${RED}❌ 多项检查失败，部署可能有问题${NC}"
    echo "请检查失败的项目并重新部署"
    exit 1
fi
