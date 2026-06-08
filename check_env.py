#!/usr/bin/env python3
"""
环境检查脚本 - 诊断Python环境和依赖问题
"""
import sys
import subprocess
import importlib

def check_python_version():
    """检查Python版本"""
    print("🐍 Python环境检查")
    print("=" * 40)
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"Python版本信息: {sys.version_info}")
    
    if sys.version_info < (3, 7):
        print("⚠️  警告: Python版本过低，建议使用Python 3.7+")
    else:
        print("✅ Python版本符合要求")
    print()

def check_pip():
    """检查pip"""
    print("📦 pip检查")
    print("=" * 40)
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pip可用: {result.stdout.strip()}")
        else:
            print(f"❌ pip不可用: {result.stderr}")
    except Exception as e:
        print(f"❌ pip检查失败: {e}")
    print()

def check_module(module_name, package_name=None):
    """检查单个模块"""
    if package_name is None:
        package_name = module_name
    
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'Unknown')
        print(f"✅ {module_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {module_name}: 未安装")
        return False

def check_dependencies():
    """检查所有依赖"""
    print("📚 依赖检查")
    print("=" * 40)
    
    dependencies = [
        ('requests', 'requests'),
        ('bs4', 'beautifulsoup4'),
        ('schedule', 'schedule'),
        ('dotenv', 'python-dotenv'),
        ('lxml', 'lxml'),
        ('PIL', 'Pillow'),
    ]
    
    missing = []
    for module_name, package_name in dependencies:
        if not check_module(module_name, package_name):
            missing.append(package_name)
    
    print()
    
    if missing:
        print("❌ 缺失的依赖:")
        for pkg in missing:
            print(f"   - {pkg}")
        print()
        print("🔧 安装命令:")
        print(f"pip install {' '.join(missing)}")
        print()
        print("或者安装所有依赖:")
        print("pip install requests beautifulsoup4 schedule python-dotenv lxml Pillow")
    else:
        print("✅ 所有依赖都已安装")
    
    return missing

def check_virtual_env():
    """检查虚拟环境"""
    print("🏠 虚拟环境检查")
    print("=" * 40)
    
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print("✅ 当前在虚拟环境中")
        print(f"   虚拟环境路径: {sys.prefix}")
    else:
        print("⚠️  当前不在虚拟环境中")
        print("   建议使用虚拟环境:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
    print()

def check_installed_packages():
    """检查已安装的包"""
    print("📋 已安装的包")
    print("=" * 40)
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"总共安装了 {len(lines)-2} 个包:")  # 减去标题行
            
            # 只显示项目相关的包
            relevant_packages = ['requests', 'beautifulsoup4', 'schedule', 'python-dotenv', 'lxml', 'Pillow']
            print("\n项目相关的包:")
            for line in lines[2:]:  # 跳过标题行
                for pkg in relevant_packages:
                    if line.lower().startswith(pkg.lower()):
                        print(f"   {line}")
        else:
            print(f"❌ 无法获取包列表: {result.stderr}")
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    print()

def provide_solutions(missing_deps):
    """提供解决方案"""
    print("🔧 解决方案")
    print("=" * 40)
    
    if missing_deps:
        print("1. 安装缺失的依赖:")
        print(f"   pip install {' '.join(missing_deps)}")
        print()
        
        print("2. 使用国内镜像源（如果网络慢）:")
        print(f"   pip install {' '.join(missing_deps)} -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        print()
        
        print("3. 如果权限问题，使用--user参数:")
        print(f"   pip install --user {' '.join(missing_deps)}")
        print()
    
    print("4. 创建并使用虚拟环境（推荐）:")
    print("   python3 -m venv venv")
    print("   source venv/bin/activate")
    print("   pip install -r requirements.txt")
    print()
    
    print("5. 验证安装:")
    print("   python3 -c \"import schedule; print('schedule安装成功')\"")
    print()

def main():
    """主函数"""
    print("🔍 IMDB监控系统环境诊断")
    print("=" * 50)
    print()
    
    check_python_version()
    check_pip()
    check_virtual_env()
    missing_deps = check_dependencies()
    check_installed_packages()
    provide_solutions(missing_deps)
    
    print("=" * 50)
    if missing_deps:
        print("❌ 发现问题，请按照上述解决方案操作")
    else:
        print("✅ 环境检查完成，所有依赖都已安装")

if __name__ == "__main__":
    main()
