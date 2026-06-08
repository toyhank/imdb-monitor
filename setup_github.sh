#!/bin/bash

# IMDB监控系统 - GitHub自动设置脚本
# 自动初始化Git仓库并推送到GitHub

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
    echo "    IMDB监控系统 - GitHub自动设置"
    echo "=================================================="
    echo -e "${NC}"
}

# 检查Git是否安装
check_git() {
    if ! command -v git &> /dev/null; then
        log_error "Git未安装，请先安装Git"
        echo "Ubuntu/Debian: sudo apt install git"
        echo "CentOS/RHEL: sudo yum install git"
        exit 1
    fi
    log_info "Git已安装: $(git --version)"
}

# 检查是否在项目目录
check_project_dir() {
    if [[ ! -f main.py ]]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    log_info "项目目录检查通过"
}

# 获取用户信息
get_user_info() {
    echo
    log_step "配置Git用户信息"
    
    # 检查现有配置
    existing_name=$(git config --global user.name 2>/dev/null || echo "")
    existing_email=$(git config --global user.email 2>/dev/null || echo "")
    
    if [[ -n "$existing_name" && -n "$existing_email" ]]; then
        log_info "现有Git配置:"
        echo "  姓名: $existing_name"
        echo "  邮箱: $existing_email"
        echo
        read -p "是否使用现有配置? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            configure_git_user
        fi
    else
        configure_git_user
    fi
}

# 配置Git用户
configure_git_user() {
    read -p "请输入你的GitHub用户名: " github_username
    read -p "请输入你的邮箱地址: " github_email
    
    git config --global user.name "$github_username"
    git config --global user.email "$github_email"
    
    log_info "Git用户信息已配置"
}

# 获取仓库信息
get_repo_info() {
    echo
    log_step "配置GitHub仓库信息"
    
    # 默认值
    default_repo_name="imdb-monitor"
    default_description="IMDB Top 250 monitoring system with notifications"
    
    read -p "仓库名称 [$default_repo_name]: " repo_name
    repo_name=${repo_name:-$default_repo_name}
    
    read -p "仓库描述 [$default_description]: " repo_description
    repo_description=${repo_description:-$default_description}
    
    read -p "GitHub用户名: " github_user
    
    REPO_URL="https://github.com/$github_user/$repo_name.git"
    
    log_info "仓库配置:"
    echo "  名称: $repo_name"
    echo "  描述: $repo_description"
    echo "  URL: $REPO_URL"
}

# 创建.gitignore文件
create_gitignore() {
    log_step "创建.gitignore文件"
    
    if [[ -f .gitignore ]]; then
        log_warn ".gitignore文件已存在，备份为.gitignore.backup"
        cp .gitignore .gitignore.backup
    fi
    
    cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
*.db
*.log
logs/
backups/
data/
temp/
*.pid

# Configuration (contains sensitive info)
config.env

# Test files
test_*.py
*_test.py
debug_*.py
check_*.py

# Temporary files
*.tmp
*.bak
*.backup
main.zip

# Build artifacts
dist/
build/
EOF
    
    log_info ".gitignore文件已创建"
}

# 创建README.md
create_readme() {
    log_step "创建README.md文件"
    
    if [[ -f README.md ]]; then
        log_warn "README.md文件已存在，备份为README.md.backup"
        cp README.md README.md.backup
    fi
    
    cat > README.md <<EOF
# 🎬 $repo_name

$repo_description

## ✨ 主要特性

- 🔍 **智能爬取**: 混合爬虫策略，结合IMDB和TMDB数据
- 📱 **企业微信通知**: 支持Markdown v2格式，图文并茂
- 📧 **邮件通知**: HTML格式邮件，支持多收件人
- 🌐 **Web界面**: 实时数据展示，Excel导出功能
- 🇨🇳 **中文支持**: 优先显示中文电影标题
- 🐳 **Docker支持**: 一键容器化部署
- 🔄 **多种部署**: systemd、supervisor、PM2、screen
- 📊 **数据增强**: TMDB API集成，丰富电影信息
- 🛡️ **稳定可靠**: 自动重启、错误恢复、健康检查

## 🚀 快速开始

### Docker部署 (推荐)

\`\`\`bash
# 1. 克隆项目
git clone $REPO_URL
cd $repo_name

# 2. 配置环境
cp config.env.example config.env
nano config.env  # 编辑配置

# 3. 启动服务
docker-compose up -d

# 4. 访问Web界面
open http://localhost:5000
\`\`\`

### Linux部署

\`\`\`bash
# 1. 克隆项目
git clone $REPO_URL
cd $repo_name

# 2. 运行部署脚本
chmod +x quick_deploy.sh
./quick_deploy.sh

# 3. 配置通知
nano config.env
\`\`\`

## 📋 系统要求

- **Python**: 3.7+
- **系统**: Linux (Ubuntu/CentOS/Fedora)
- **内存**: 512MB+ (推荐1GB)
- **存储**: 1GB可用空间
- **网络**: 稳定的互联网连接

## ⚙️ 配置说明

### 企业微信通知

\`\`\`bash
# 在企业微信群中添加机器人，获取Webhook URL
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
NOTIFICATION_TYPE=webhook
\`\`\`

### 邮件通知

\`\`\`bash
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com
NOTIFICATION_TYPE=email
\`\`\`

## 📚 文档

- [Linux部署指南](LINUX_DEPLOYMENT_GUIDE.md)
- [快速部署说明](QUICK_DEPLOY.md)
- [Web服务管理](WEB_SERVICE_GUIDE.md)
- [GitHub设置指南](GITHUB_SETUP.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目采用MIT许可证

---

**如果这个项目对你有帮助，请给个⭐️支持一下！**
EOF
    
    log_info "README.md文件已创建"
}

# 初始化Git仓库
init_git_repo() {
    log_step "初始化Git仓库"
    
    if [[ -d .git ]]; then
        log_warn "Git仓库已存在"
        read -p "是否重新初始化? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .git
            git init
            log_info "Git仓库已重新初始化"
        fi
    else
        git init
        log_info "Git仓库已初始化"
    fi
    
    # 设置默认分支为main
    git branch -M main
    
    # 添加远程仓库
    if git remote get-url origin &>/dev/null; then
        git remote set-url origin "$REPO_URL"
        log_info "远程仓库URL已更新"
    else
        git remote add origin "$REPO_URL"
        log_info "远程仓库已添加"
    fi
}

# 提交文件
commit_files() {
    log_step "添加和提交文件"
    
    # 添加所有文件
    git add .
    
    # 显示将要提交的文件
    echo "将要提交的文件:"
    git status --short
    echo
    
    read -p "是否继续提交? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_warn "用户取消提交"
        exit 0
    fi
    
    # 提交文件
    commit_message="Initial commit: IMDB Top 250 monitoring system

Features:
- IMDB Top 250 scraping with hybrid approach
- Enterprise WeChat notifications with Markdown v2 format
- Email notifications support
- Web interface with real-time data and Excel export
- TMDB API integration for enhanced movie data
- Chinese title support
- Docker deployment support
- Multiple deployment options (systemd, supervisor, PM2, screen)
- Automatic service monitoring and restart
- Comprehensive logging and error handling"
    
    git commit -m "$commit_message"
    log_info "文件已提交到本地仓库"
}

# 推送到GitHub
push_to_github() {
    log_step "推送到GitHub"
    
    echo "请确保你已在GitHub上创建了仓库: $REPO_URL"
    echo "如果还没有创建，请:"
    echo "1. 访问 https://github.com/new"
    echo "2. 仓库名称: $repo_name"
    echo "3. 描述: $repo_description"
    echo "4. 选择 Public 或 Private"
    echo "5. 不要勾选 'Initialize this repository with a README'"
    echo "6. 点击 'Create repository'"
    echo
    
    read -p "仓库已创建，按回车继续推送..."
    
    # 推送到GitHub
    if git push -u origin main; then
        log_success "代码已成功推送到GitHub!"
    else
        log_warn "推送失败，尝试强制推送..."
        read -p "是否强制推送? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push -u origin main --force
            log_success "代码已强制推送到GitHub!"
        else
            log_error "推送失败，请手动解决冲突"
            exit 1
        fi
    fi
}

# 显示完成信息
show_completion_info() {
    echo
    log_success "GitHub设置完成!"
    echo
    echo "=========================================="
    echo "仓库信息:"
    echo "  GitHub URL: $REPO_URL"
    echo "  本地目录: $(pwd)"
    echo
    echo "下一步操作:"
    echo "1. 访问GitHub仓库: $REPO_URL"
    echo "2. 添加仓库描述和标签"
    echo "3. 设置GitHub Pages (可选)"
    echo "4. 配置GitHub Actions (可选)"
    echo
    echo "日常使用:"
    echo "  git add .                    # 添加更改"
    echo "  git commit -m '描述'         # 提交更改"
    echo "  git push                     # 推送到GitHub"
    echo
    echo "更多信息请查看: GITHUB_SETUP.md"
    echo "=========================================="
}

# 主函数
main() {
    show_banner
    check_git
    check_project_dir
    get_user_info
    get_repo_info
    create_gitignore
    create_readme
    init_git_repo
    commit_files
    push_to_github
    show_completion_info
}

# 运行主函数
main "$@"
