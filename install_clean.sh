#!/bin/bash

# IMDB监控系统 - 清洁安装脚本
# 解决 "destination path '.' already exists and is not an empty directory" 错误

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

echo -e "${BLUE}"
echo "=================================================="
echo "    IMDB监控系统 - 本地安装"
echo "    (使用当前目录的项目文件)"
echo "=================================================="
echo -e "${NC}"

# 使用当前目录作为项目目录
PROJECT_DIR="$(pwd)"
log_info "使用当前目录: $PROJECT_DIR"

# 检查必要文件
log_step "检查项目文件..."
missing_files=()
[[ ! -f main.py ]] && missing_files+=("main.py")
[[ ! -f requirements.txt ]] && missing_files+=("requirements.txt")
[[ ! -f config.env.example ]] && missing_files+=("config.env.example")

if [[ ${#missing_files[@]} -gt 0 ]]; then
    log_error "缺少必要文件: ${missing_files[*]}"
    log_error "请确保在项目根目录运行此脚本"
    exit 1
fi

log_info "项目文件检查通过"

# 停止可能运行的服务
if systemctl is-active imdb-monitor &>/dev/null; then
    log_info "停止systemd服务..."
    sudo systemctl stop imdb-monitor
fi

# 创建配置文件（如果不存在）
if [[ ! -f config.env ]]; then
    if [[ -f config.env.example ]]; then
        cp config.env.example config.env
        log_info "已从示例创建config.env文件"
    else
        log_warn "未找到config.env.example文件"
    fi
fi

# 安装Python依赖
log_step "设置Python环境..."

# 检查Python
if ! command -v python3 &>/dev/null; then
    log_error "Python3未安装，请先安装Python3"
    exit 1
fi

# 创建虚拟环境
log_info "创建Python虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
log_info "升级pip..."
pip install --upgrade pip

# 安装依赖
if [[ -f requirements.txt ]]; then
    log_info "安装Python依赖..."
    pip install -r requirements.txt
else
    log_error "requirements.txt文件不存在"
    exit 1
fi

# 设置权限
log_step "设置文件权限..."
find . -type f -name "*.py" -exec chmod 644 {} \;
find . -type f -name "*.sh" -exec chmod 755 {} \;
find . -type d -exec chmod 755 {} \;

# 创建必要目录
mkdir -p logs backups data

# 测试安装
log_step "测试安装..."
if python -c "import main; print('导入成功')" &>/dev/null; then
    log_info "Python模块导入测试通过"
else
    log_error "Python模块导入测试失败"
    exit 1
fi

# 显示完成信息
echo
log_info "清洁安装完成！"
echo
echo "=========================================="
echo "安装信息:"
echo "  项目目录: $PROJECT_DIR"
echo "  配置文件: $PROJECT_DIR/config.env"
echo "  虚拟环境: $PROJECT_DIR/venv"
if [[ -n "${BACKUP_DIR:-}" ]]; then
    echo "  备份目录: $BACKUP_DIR"
fi
echo
echo "下一步操作:"
echo "1. 编辑配置文件:"
echo "   nano $PROJECT_DIR/config.env"
echo
echo "2. 测试运行:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python main.py --once"
echo
echo "3. 启动Web界面:"
echo "   python main.py --web"
echo
echo "4. 设置系统服务 (可选):"
echo "   sudo ./deploy_linux.sh"
echo "=========================================="

# 提示编辑配置
echo
read -p "是否现在编辑配置文件? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v nano &>/dev/null; then
        nano config.env
    elif command -v vi &>/dev/null; then
        vi config.env
    else
        log_warn "未找到文本编辑器，请手动编辑 config.env 文件"
    fi
fi

log_info "安装脚本执行完成！"
