#!/bin/bash

# SQLite数据库权限修复脚本

echo "🗄️ 修复SQLite数据库权限问题"
echo "================================"

# 获取当前用户和目录
CURRENT_USER=$(whoami)
PROJECT_DIR=$(pwd)
DB_FILE="imdb_top250.db"

echo "当前用户: $CURRENT_USER"
echo "项目目录: $PROJECT_DIR"
echo "数据库文件: $DB_FILE"
echo ""

# 1. 检查磁盘空间
echo "💾 检查磁盘空间..."
df -h .
echo ""

# 2. 检查当前权限状态
echo "🔍 检查当前权限状态..."
echo "目录权限:"
ls -ld .
echo ""

if [ -f "$DB_FILE" ]; then
    echo "数据库文件权限:"
    ls -la "$DB_FILE"
    echo ""
    
    echo "数据库文件详细信息:"
    file "$DB_FILE"
    echo "文件大小: $(du -h "$DB_FILE" | cut -f1)"
else
    echo "⚠️  数据库文件不存在"
fi
echo ""

# 3. 修复目录权限
echo "📁 修复目录权限..."
chmod 755 "$PROJECT_DIR"
if [ $? -eq 0 ]; then
    echo "✅ 目录权限已设置为 755"
else
    echo "❌ 目录权限设置失败"
fi
echo ""

# 4. 处理数据库文件
if [ -f "$DB_FILE" ]; then
    echo "🗄️ 修复现有数据库文件权限..."
    
    # 设置文件权限
    chmod 666 "$DB_FILE"
    if [ $? -eq 0 ]; then
        echo "✅ 数据库文件权限已设置为 666"
    else
        echo "❌ 数据库文件权限设置失败"
    fi
    
    # 更改所有者
    if [ "$CURRENT_USER" != "root" ]; then
        sudo chown "$CURRENT_USER:$CURRENT_USER" "$DB_FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ 数据库文件所有者已更改为 $CURRENT_USER"
        else
            echo "⚠️  无法更改数据库文件所有者（可能不需要sudo权限）"
        fi
    fi
    
    # 检查数据库是否可写
    echo ""
    echo "🧪 测试数据库写入权限..."
    if [ -w "$DB_FILE" ]; then
        echo "✅ 数据库文件可写"
    else
        echo "❌ 数据库文件不可写"
    fi
    
    # 尝试用SQLite命令测试
    if command -v sqlite3 &> /dev/null; then
        echo ""
        echo "🧪 测试SQLite数据库连接..."
        if sqlite3 "$DB_FILE" "SELECT 1;" &>/dev/null; then
            echo "✅ SQLite数据库连接正常"
        else
            echo "❌ SQLite数据库连接失败"
            echo "可能需要重新创建数据库"
        fi
    fi
    
else
    echo "📝 数据库文件不存在，将在首次运行时创建"
fi
echo ""

# 5. 检查并修复相关文件权限
echo "📋 检查其他相关文件权限..."

# 日志文件
if [ -f "imdb_monitor.log" ]; then
    chmod 666 imdb_monitor.log
    echo "✅ 日志文件权限已修复"
fi

# 配置文件
if [ -f "config.env" ]; then
    chmod 600 config.env
    echo "✅ 配置文件权限已修复"
fi

# Python文件
chmod 644 *.py 2>/dev/null
echo "✅ Python文件权限已修复"

echo ""

# 6. 创建数据库备份目录
echo "💾 创建备份目录..."
mkdir -p backups
chmod 755 backups
echo "✅ 备份目录已创建"
echo ""

# 7. 提供解决方案选项
echo "🔧 解决方案选项:"
echo "================================"
echo ""

if [ -f "$DB_FILE" ]; then
    echo "选项1: 重新创建数据库（推荐）"
    echo "  备份: cp $DB_FILE backups/${DB_FILE}.$(date +%Y%m%d_%H%M%S)"
    echo "  删除: rm $DB_FILE"
    echo "  运行: python main.py --once"
    echo ""
    
    echo "选项2: 手动修复权限"
    echo "  sudo chown $CURRENT_USER:$CURRENT_USER $DB_FILE"
    echo "  chmod 666 $DB_FILE"
    echo "  chmod 755 ."
    echo ""
    
    echo "选项3: 检查数据库完整性"
    echo "  sqlite3 $DB_FILE 'PRAGMA integrity_check;'"
    echo ""
fi

echo "选项4: 使用不同的数据库路径"
echo "  在config.env中设置: DATABASE_PATH=/tmp/imdb_top250.db"
echo "  或: DATABASE_PATH=\$HOME/imdb_top250.db"
echo ""

# 8. 显示最终状态
echo "📊 最终权限状态:"
echo "================================"
ls -la | grep -E "\.(db|log|env)$|^d.*\.$"
echo ""

echo "🎯 建议的下一步操作:"
if [ -f "$DB_FILE" ]; then
    echo "1. 备份现有数据库: cp $DB_FILE backups/"
    echo "2. 删除数据库文件: rm $DB_FILE"
    echo "3. 重新运行程序: python main.py --once"
else
    echo "1. 确保在虚拟环境中: source venv/bin/activate"
    echo "2. 运行程序: python main.py --once"
fi
echo ""

echo "✅ 数据库权限修复脚本执行完成"
