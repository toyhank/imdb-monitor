#!/bin/bash

# IMDB监控系统部署修复脚本
# 解决常见的部署问题

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
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 显示帮助信息
show_help() {
    echo "IMDB监控系统部署修复脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -c, --clean          清理现有安装"
    echo "  -r, --reinstall      重新安装"
    echo "  -f, --fix-git        修复Git问题"
    echo "  -d, --fix-deps       修复依赖问题"
    echo "  -p, --fix-perms      修复权限问题"
    echo "  -h, --help           显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 --clean          # 清理现有安装"
    echo "  $0 --reinstall      # 完全重新安装"
    echo "  $0 --fix-git        # 仅修复Git问题"
}

# 检测项目目录
detect_project_dir() {
    local dirs=(
        "$HOME/imdb-monitor"
        "/opt/imdb-monitor"
        "$(pwd)"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            if [[ -f "$dir/main.py" || -f "$dir/requirements.txt" ]]; then
                PROJECT_DIR="$dir"
                return 0
            fi
        fi
    done
    
    # 如果没找到，使用默认目录
    PROJECT_DIR="$HOME/imdb-monitor"
    return 1
}

# 清理现有安装
clean_installation() {
    log_step "清理现有安装..."
    
    detect_project_dir
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_info "找到项目目录: $PROJECT_DIR"
        
        # 备份重要文件
        backup_dir="$PROJECT_DIR.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "创建备份: $backup_dir"
        
        mkdir -p "$backup_dir"
        [[ -f "$PROJECT_DIR/config.env" ]] && cp "$PROJECT_DIR/config.env" "$backup_dir/"
        [[ -f "$PROJECT_DIR/imdb_data.db" ]] && cp "$PROJECT_DIR/imdb_data.db" "$backup_dir/"
        [[ -d "$PROJECT_DIR/logs" ]] && cp -r "$PROJECT_DIR/logs" "$backup_dir/"
        
        # 停止服务
        if systemctl is-active imdb-monitor &>/dev/null; then
            log_info "停止systemd服务..."
            sudo systemctl stop imdb-monitor
        fi
        
        # 删除项目目录
        log_info "删除项目目录..."
        rm -rf "$PROJECT_DIR"
        
        log_info "清理完成，备份保存在: $backup_dir"
    else
        log_warn "未找到现有安装"
    fi
}

# 修复Git问题
fix_git_issues() {
    log_step "修复Git问题..."
    
    detect_project_dir
    cd "$PROJECT_DIR" 2>/dev/null || {
        log_error "项目目录不存在: $PROJECT_DIR"
        return 1
    }
    
    # 备份配置文件
    [[ -f config.env ]] && cp config.env config.env.backup
    
    if [[ -d .git ]]; then
        log_info "重置Git仓库..."
        git reset --hard HEAD
        git clean -fd
        git pull origin main || {
            log_warn "Git pull失败，尝试重新克隆..."
            cd ..
            rm -rf "$PROJECT_DIR"
            mkdir -p "$PROJECT_DIR"
            cd "$PROJECT_DIR"
            git clone https://github.com/your-username/imdb-monitor.git .
        }
    else
        log_info "初始化Git仓库..."
        # 如果目录不为空，先清理
        if [[ "$(ls -A .)" ]]; then
            find . -mindepth 1 -maxdepth 1 ! -name 'config.env*' ! -name '*.db' ! -name 'logs' -exec rm -rf {} +
        fi
        git clone https://github.com/your-username/imdb-monitor.git .
    fi
    
    # 恢复配置文件
    [[ -f config.env.backup ]] && mv config.env.backup config.env
    
    log_info "Git问题修复完成"
}

# 修复依赖问题
fix_dependencies() {
    log_step "修复依赖问题..."
    
    detect_project_dir
    cd "$PROJECT_DIR" 2>/dev/null || {
        log_error "项目目录不存在: $PROJECT_DIR"
        return 1
    }
    
    # 检查虚拟环境
    if [[ -d venv ]]; then
        log_info "重新创建虚拟环境..."
        rm -rf venv
    fi
    
    # 创建新的虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [[ -f requirements.txt ]]; then
        log_info "安装Python依赖..."
        pip install -r requirements.txt
    else
        log_error "requirements.txt文件不存在"
        return 1
    fi
    
    log_info "依赖问题修复完成"
}

# 修复权限问题
fix_permissions() {
    log_step "修复权限问题..."
    
    detect_project_dir
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_info "修复目录权限..."
        
        # 修复目录所有权
        if [[ "$PROJECT_DIR" == "/opt/"* ]]; then
            sudo chown -R $USER:$USER "$PROJECT_DIR"
        fi
        
        # 修复文件权限
        find "$PROJECT_DIR" -type f -name "*.py" -exec chmod 644 {} \;
        find "$PROJECT_DIR" -type f -name "*.sh" -exec chmod 755 {} \;
        
        # 修复目录权限
        find "$PROJECT_DIR" -type d -exec chmod 755 {} \;
        
        # 确保数据目录可写
        mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/backups"
        chmod 755 "$PROJECT_DIR/logs" "$PROJECT_DIR/backups"
        
        log_info "权限问题修复完成"
    else
        log_error "项目目录不存在"
        return 1
    fi
}

# 重新安装
reinstall() {
    log_step "开始重新安装..."
    
    # 清理现有安装
    clean_installation
    
    # 重新下载和安装
    log_info "重新下载项目..."
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # 下载项目文件
    if command -v git &>/dev/null; then
        git clone https://github.com/your-username/imdb-monitor.git .
    else
        curl -L https://github.com/your-username/imdb-monitor/archive/main.zip -o main.zip
        unzip -q main.zip
        mv imdb-monitor-main/* .
        rm -rf imdb-monitor-main main.zip
    fi
    
    # 恢复配置文件
    backup_dir=$(ls -d "$PROJECT_DIR".backup.* 2>/dev/null | tail -1)
    if [[ -n "$backup_dir" && -f "$backup_dir/config.env" ]]; then
        cp "$backup_dir/config.env" "$PROJECT_DIR/"
        log_info "已恢复配置文件"
    fi
    
    # 修复依赖
    fix_dependencies
    
    # 修复权限
    fix_permissions
    
    log_info "重新安装完成"
}

# 诊断问题
diagnose_issues() {
    log_step "诊断部署问题..."
    
    echo "系统信息:"
    echo "  操作系统: $(uname -a)"
    echo "  Python版本: $(python3 --version 2>/dev/null || echo '未安装')"
    echo "  Git版本: $(git --version 2>/dev/null || echo '未安装')"
    echo
    
    detect_project_dir
    echo "项目信息:"
    echo "  项目目录: $PROJECT_DIR"
    echo "  目录存在: $([[ -d "$PROJECT_DIR" ]] && echo '是' || echo '否')"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        cd "$PROJECT_DIR"
        echo "  main.py存在: $([[ -f main.py ]] && echo '是' || echo '否')"
        echo "  config.env存在: $([[ -f config.env ]] && echo '是' || echo '否')"
        echo "  虚拟环境存在: $([[ -d venv ]] && echo '是' || echo '否')"
        echo "  Git仓库: $([[ -d .git ]] && echo '是' || echo '否')"
        
        if [[ -d .git ]]; then
            echo "  Git状态: $(git status --porcelain | wc -l) 个修改文件"
            echo "  Git远程: $(git remote get-url origin 2>/dev/null || echo '未设置')"
        fi
    fi
    
    echo
    echo "服务状态:"
    echo "  systemd服务: $(systemctl is-active imdb-monitor 2>/dev/null || echo '未运行')"
    echo "  Docker容器: $(docker ps --filter name=imdb-monitor --format 'table {{.Status}}' 2>/dev/null | tail -n +2 || echo '未运行')"
}

# 主函数
main() {
    case "${1:-}" in
        -c|--clean)
            clean_installation
            ;;
        -r|--reinstall)
            reinstall
            ;;
        -f|--fix-git)
            fix_git_issues
            ;;
        -d|--fix-deps)
            fix_dependencies
            ;;
        -p|--fix-perms)
            fix_permissions
            ;;
        -h|--help)
            show_help
            ;;
        "")
            # 如果没有参数，运行诊断
            diagnose_issues
            echo
            echo "请使用 $0 --help 查看可用选项"
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
