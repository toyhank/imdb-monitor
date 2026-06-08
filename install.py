"""
安装和配置脚本
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        return False
    print(f"✓ Python版本: {sys.version}")
    return True

def install_dependencies():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: 依赖包安装失败: {e}")
        return False

def setup_config():
    """设置配置文件"""
    config_file = "config.env"
    if os.path.exists(config_file):
        print(f"✓ 配置文件 {config_file} 已存在")
        return True
    
    print("配置文件不存在，请手动编辑 config.env 文件")
    return True

def test_installation():
    """测试安装"""
    print("正在测试安装...")
    try:
        # 运行演示脚本
        result = subprocess.run([sys.executable, "demo.py"], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ 安装测试通过")
            return True
        else:
            print(f"错误: 测试失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("警告: 测试超时，可能是网络问题")
        return True
    except Exception as e:
        print(f"错误: 测试失败: {e}")
        return False

def create_service_script():
    """创建服务脚本"""
    if os.name == 'nt':  # Windows
        script_content = f"""@echo off
cd /d "{os.getcwd()}"
python main.py
pause
"""
        with open("start_monitor.bat", "w", encoding="utf-8") as f:
            f.write(script_content)
        print("✓ 创建了 start_monitor.bat 启动脚本")
    else:  # Linux/Mac
        script_content = f"""#!/bin/bash
cd "{os.getcwd()}"
python3 main.py
"""
        with open("start_monitor.sh", "w") as f:
            f.write(script_content)
        os.chmod("start_monitor.sh", 0o755)
        print("✓ 创建了 start_monitor.sh 启动脚本")

def print_usage_instructions():
    """打印使用说明"""
    print("\n" + "="*50)
    print("安装完成！使用说明:")
    print("="*50)
    
    print("\n1. 配置通知:")
    print("   编辑 config.env 文件，设置 WEBHOOK_URL 或邮件配置")
    
    print("\n2. 运行方式:")
    print("   - 定时监控: python main.py")
    print("   - 执行一次: python main.py --once")
    print("   - 演示模式: python demo.py")
    
    if os.name == 'nt':
        print("   - 或双击 start_monitor.bat")
    else:
        print("   - 或运行 ./start_monitor.sh")
    
    print("\n3. 配置示例:")
    print("   Webhook: WEBHOOK_URL=https://your-webhook.com/notify")
    print("   邮件: EMAIL_USERNAME=your@gmail.com")
    
    print("\n4. 日志文件:")
    print("   - 程序日志: imdb_monitor.log")
    print("   - 数据库: imdb_top250.db")
    
    print("\n5. 测试:")
    print("   python test_monitor.py")

def main():
    """主安装函数"""
    print("IMDB Top 250 监控程序安装脚本")
    print("="*40)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 设置配置
    setup_config()
    
    # 创建启动脚本
    create_service_script()
    
    # 测试安装
    test_installation()
    
    # 打印使用说明
    print_usage_instructions()

if __name__ == "__main__":
    main()
