#!/bin/bash

# IMDB监控系统权限修复脚本

echo "🔧 修复IMDB监控系统文件权限"
echo "================================"

# 获取当前用户
CURRENT_USER=$(whoami)
echo "当前用户: $CURRENT_USER"

# 获取项目目录
PROJECT_DIR=$(pwd)
echo "项目目录: $PROJECT_DIR"

# 1. 修复项目目录权限
echo ""
echo "📁 修复项目目录权限..."
chmod 755 "$PROJECT_DIR"
echo "✅ 项目目录权限已设置为 755"

# 2. 修复Python文件权限
echo ""
echo "🐍 修复Python文件权限..."
find . -name "*.py" -exec chmod 644 {} \;
echo "✅ Python文件权限已设置为 644"

# 3. 修复可执行脚本权限
echo ""
echo "📜 修复脚本文件权限..."
chmod +x main.py 2>/dev/null || true
chmod +x *.sh 2>/dev/null || true
echo "✅ 脚本文件权限已设置为可执行"

# 4. 修复配置文件权限
echo ""
echo "⚙️ 修复配置文件权限..."
if [ -f "config.env" ]; then
    chmod 600 config.env
    echo "✅ config.env 权限已设置为 600 (仅所有者可读写)"
else
    echo "⚠️  config.env 文件不存在"
fi

# 5. 处理日志文件
echo ""
echo "📝 处理日志文件权限..."

# 检查日志文件是否存在
if [ -f "imdb_monitor.log" ]; then
    echo "日志文件已存在，修复权限..."
    chmod 644 imdb_monitor.log
    chown $CURRENT_USER:$CURRENT_USER imdb_monitor.log 2>/dev/null || true
    echo "✅ imdb_monitor.log 权限已修复"
else
    echo "日志文件不存在，创建并设置权限..."
    touch imdb_monitor.log
    chmod 644 imdb_monitor.log
    echo "✅ imdb_monitor.log 已创建并设置权限"
fi

# 6. 处理数据库文件
echo ""
echo "🗄️ 处理数据库文件权限..."
if [ -f "imdb_top250.db" ]; then
    chmod 644 imdb_top250.db
    chown $CURRENT_USER:$CURRENT_USER imdb_top250.db 2>/dev/null || true
    echo "✅ 数据库文件权限已修复"
else
    echo "ℹ️  数据库文件不存在（首次运行时会创建）"
fi

# 7. 处理虚拟环境权限
echo ""
echo "🐍 处理虚拟环境权限..."
if [ -d "venv" ]; then
    find venv -type d -exec chmod 755 {} \; 2>/dev/null || true
    find venv -type f -exec chmod 644 {} \; 2>/dev/null || true
    find venv/bin -type f -exec chmod 755 {} \; 2>/dev/null || true
    echo "✅ 虚拟环境权限已修复"
else
    echo "⚠️  虚拟环境不存在"
fi

# 8. 创建日志目录（可选）
echo ""
echo "📂 创建日志目录..."
mkdir -p logs
chmod 755 logs
echo "✅ logs目录已创建"

# 9. 显示当前权限状态
echo ""
echo "📋 当前文件权限状态:"
echo "================================"
ls -la | grep -E "\.(py|sh|env|log|db)$|^d"

echo ""
echo "🎉 权限修复完成！"
echo ""
echo "📝 权限说明:"
echo "  - 目录: 755 (rwxr-xr-x) - 所有者可读写执行，其他人可读执行"
echo "  - Python文件: 644 (rw-r--r--) - 所有者可读写，其他人只读"
echo "  - 配置文件: 600 (rw-------) - 仅所有者可读写"
echo "  - 日志文件: 644 (rw-r--r--) - 所有者可读写，其他人只读"
echo "  - 可执行文件: 755 (rwxr-xr-x) - 所有者可读写执行，其他人可读执行"
echo ""
echo "🚀 现在可以运行程序了:"
echo "  source venv/bin/activate"
echo "  python main.py --once"
