#!/usr/bin/env python3
"""
切换统计界面显示状态的工具脚本
用于快速启用或禁用Web界面中的统计相关控件
"""

import os
import sys
import argparse


def read_env_file(file_path):
    """读取环境变量文件"""
    env_vars = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def write_env_file(file_path, env_vars):
    """写入环境变量文件"""
    lines = []
    
    # 如果文件存在，保留注释和格式
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                    key = line_stripped.split('=', 1)[0].strip()
                    if key in env_vars:
                        lines.append(f"{key}={env_vars[key]}\n")
                        del env_vars[key]  # 标记为已处理
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
    
    # 添加新的环境变量
    for key, value in env_vars.items():
        lines.append(f"{key}={value}\n")
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def get_current_status(config_file):
    """获取当前统计界面显示状态"""
    env_vars = read_env_file(config_file)
    
    enable_analytics = env_vars.get('ENABLE_ANALYTICS', 'false').lower() == 'true'
    show_analytics_ui = env_vars.get('SHOW_ANALYTICS_UI', 'false').lower() == 'true'
    analytics_id = env_vars.get('GOOGLE_ANALYTICS_ID', '')
    
    return {
        'enable_analytics': enable_analytics,
        'show_analytics_ui': show_analytics_ui,
        'analytics_id': analytics_id,
        'config_file': config_file
    }


def set_analytics_ui_status(config_file, show_ui, enable_analytics=None):
    """设置统计界面显示状态"""
    env_vars = read_env_file(config_file)
    
    # 更新显示状态
    env_vars['SHOW_ANALYTICS_UI'] = 'true' if show_ui else 'false'
    
    # 如果指定了启用状态，也更新它
    if enable_analytics is not None:
        env_vars['ENABLE_ANALYTICS'] = 'true' if enable_analytics else 'false'
    
    # 写入文件
    write_env_file(config_file, env_vars)
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='切换IMDB监控系统中统计界面的显示状态',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python toggle_analytics_ui.py --status                    # 查看当前状态
  python toggle_analytics_ui.py --hide                      # 隐藏统计界面
  python toggle_analytics_ui.py --show                      # 显示统计界面
  python toggle_analytics_ui.py --hide --disable-analytics  # 隐藏界面并禁用统计
  python toggle_analytics_ui.py --show --enable-analytics   # 显示界面并启用统计
        """
    )
    
    parser.add_argument('--config', '-c', 
                       default='config.env',
                       help='配置文件路径 (默认: config.env)')
    
    parser.add_argument('--status', '-s',
                       action='store_true',
                       help='显示当前状态')
    
    parser.add_argument('--show',
                       action='store_true',
                       help='显示统计界面')
    
    parser.add_argument('--hide',
                       action='store_true',
                       help='隐藏统计界面')
    
    parser.add_argument('--enable-analytics',
                       action='store_true',
                       help='启用Google Analytics统计')
    
    parser.add_argument('--disable-analytics',
                       action='store_true',
                       help='禁用Google Analytics统计')
    
    args = parser.parse_args()
    
    # 检查配置文件
    if not os.path.exists(args.config):
        print(f"❌ 配置文件不存在: {args.config}")
        print(f"请先复制示例配置文件: cp config.env.example {args.config}")
        sys.exit(1)
    
    # 获取当前状态
    current_status = get_current_status(args.config)
    
    # 显示当前状态
    if args.status or (not args.show and not args.hide):
        print("📊 IMDB监控系统 - 统计界面状态")
        print("=" * 40)
        print(f"配置文件: {current_status['config_file']}")
        print(f"Google Analytics: {'✅ 已启用' if current_status['enable_analytics'] else '❌ 已禁用'}")
        print(f"统计界面显示: {'✅ 显示' if current_status['show_analytics_ui'] else '❌ 隐藏'}")
        print(f"跟踪ID: {current_status['analytics_id'] if current_status['analytics_id'] else '未配置'}")
        print()
        
        if current_status['enable_analytics'] and not current_status['analytics_id']:
            print("⚠️  警告: 已启用统计但未配置跟踪ID")
        
        if not args.show and not args.hide:
            print("💡 使用 --show 或 --hide 来切换界面显示状态")
        
        if not (args.show or args.hide):
            return
    
    # 执行操作
    try:
        if args.show:
            print("🔄 显示统计界面...")
            enable_analytics = None
            if args.enable_analytics:
                enable_analytics = True
                print("🔄 启用Google Analytics...")
            elif args.disable_analytics:
                enable_analytics = False
                print("🔄 禁用Google Analytics...")
            
            set_analytics_ui_status(args.config, True, enable_analytics)
            print("✅ 统计界面已设置为显示")
            
        elif args.hide:
            print("🔄 隐藏统计界面...")
            enable_analytics = None
            if args.enable_analytics:
                enable_analytics = True
                print("🔄 启用Google Analytics...")
            elif args.disable_analytics:
                enable_analytics = False
                print("🔄 禁用Google Analytics...")
            
            set_analytics_ui_status(args.config, False, enable_analytics)
            print("✅ 统计界面已设置为隐藏")
        
        # 显示更新后的状态
        print("\n📊 更新后的状态:")
        updated_status = get_current_status(args.config)
        print(f"Google Analytics: {'✅ 已启用' if updated_status['enable_analytics'] else '❌ 已禁用'}")
        print(f"统计界面显示: {'✅ 显示' if updated_status['show_analytics_ui'] else '❌ 隐藏'}")
        
        print("\n💡 提示:")
        print("- 更改将在下次重启Web服务后生效")
        print("- 重启命令: python main.py --web")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
