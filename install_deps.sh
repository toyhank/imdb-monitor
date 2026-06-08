#!/bin/bash

# IMDB监控系统依赖安装脚本

echo "🚀 安装IMDB监控系统依赖..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
fi

echo "✅ Python3已安装: $(python3 --version)"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3未安装，请先安装pip3"
    exit 1
fi

echo "✅ pip3已安装: $(pip3 --version)"

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境？(推荐) [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
fi

# 升级pip
echo "📦 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装项目依赖..."

# 核心依赖
DEPS="requests beautifulsoup4 schedule python-dotenv lxml Pillow"

# 尝试使用国内镜像源
echo "尝试使用清华镜像源..."
if pip install $DEPS -i https://pypi.tuna.tsinghua.edu.cn/simple/; then
    echo "✅ 依赖安装成功（清华镜像源）"
else
    echo "⚠️  清华镜像源失败，尝试默认源..."
    if pip install $DEPS; then
        echo "✅ 依赖安装成功（默认源）"
    else
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 验证安装
echo "🧪 验证安装..."
python3 -c "
import requests, bs4, schedule, dotenv, lxml, PIL
print('✅ 所有依赖验证成功')
print('requests:', requests.__version__)
print('beautifulsoup4:', bs4.__version__)
print('schedule:', schedule.__version__)
"

if [ $? -eq 0 ]; then
    echo "🎉 安装完成！"
    echo ""
    echo "下一步："
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "1. 激活虚拟环境: source venv/bin/activate"
    fi
    echo "2. 配置config.env文件"
    echo "3. 运行程序: python3 main.py --once"
else
    echo "❌ 验证失败，请检查安装"
    exit 1
fi
