#!/usr/bin/env python3
"""
验证Google Analytics统计功能
快速检查统计代码是否正确注入和工作
"""

import requests
import re
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config.env')


def verify_analytics_injection(url="http://localhost:5000"):
    """验证统计代码注入"""
    print(f"🔍 验证Google Analytics代码注入: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ 页面访问失败: {response.status_code}")
            return False
        
        content = response.text
        print(f"✅ 页面访问成功，大小: {len(content)} 字符")
        
        # 检查Google Analytics脚本
        checks = [
            {
                'name': 'Google Analytics脚本加载',
                'pattern': r'googletagmanager\.com/gtag/js\?id=G-[A-Z0-9]+',
                'required': True
            },
            {
                'name': 'gtag函数定义',
                'pattern': r'function gtag\(\)',
                'required': True
            },
            {
                'name': '跟踪ID配置',
                'pattern': r'gtag\(\'config\',\s*\'G-[A-Z0-9]+\'',
                'required': True
            },
            {
                'name': 'IP匿名化',
                'pattern': r'anonymize_ip.*true',
                'required': True
            },
            {
                'name': '外部链接跟踪',
                'pattern': r'external_link',
                'required': False
            },
            {
                'name': '文件下载跟踪',
                'pattern': r'file_download',
                'required': False
            },
            {
                'name': '搜索跟踪',
                'pattern': r'site_search',
                'required': False
            },
            {
                'name': '滚动跟踪',
                'pattern': r'scroll.*engagement',
                'required': False
            }
        ]
        
        results = []
        for check in checks:
            found = re.search(check['pattern'], content, re.IGNORECASE)
            status = "✅" if found else ("❌" if check['required'] else "⚠️")
            results.append({
                'name': check['name'],
                'found': bool(found),
                'required': check['required'],
                'status': status
            })
            print(f"  {status} {check['name']}")
        
        # 提取跟踪ID
        tracking_id_match = re.search(r'G-[A-Z0-9]+', content)
        if tracking_id_match:
            tracking_id = tracking_id_match.group()
            print(f"  📊 跟踪ID: {tracking_id}")
        
        # 检查代码位置
        head_match = re.search(r'<head>(.*?)</head>', content, re.DOTALL)
        if head_match and 'gtag' in head_match.group(1):
            print(f"  ✅ 统计代码位于<head>部分")
        else:
            print(f"  ⚠️  统计代码可能不在<head>部分")
        
        # 统计结果
        required_passed = sum(1 for r in results if r['required'] and r['found'])
        required_total = sum(1 for r in results if r['required'])
        optional_passed = sum(1 for r in results if not r['required'] and r['found'])
        optional_total = sum(1 for r in results if not r['required'])
        
        print(f"\n📊 检查结果:")
        print(f"  必需项: {required_passed}/{required_total} 通过")
        print(f"  可选项: {optional_passed}/{optional_total} 通过")
        
        success = required_passed == required_total
        if success:
            print(f"  🎉 Google Analytics代码注入成功！")
        else:
            print(f"  ❌ 存在必需项未通过，请检查配置")
        
        return success
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Web服务器")
        print("请确保Web服务器正在运行: python main.py --web")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def verify_browser_instructions():
    """提供浏览器验证说明"""
    print(f"\n🌐 浏览器验证步骤:")
    print("-" * 30)
    print("1. 打开浏览器访问: http://localhost:5000")
    print("2. 按F12打开开发者工具")
    print("3. 在Console标签中输入: typeof gtag")
    print("   - 应该返回 'function'")
    print("4. 在Network标签中刷新页面")
    print("   - 查看是否有googletagmanager.com的请求")
    print("5. 在Elements标签中查看<head>部分")
    print("   - 确认包含Google Analytics脚本")
    print("6. 测试事件跟踪:")
    print("   - 在Console中输入: gtag('event', 'test', {event_category: 'manual'})")
    print("   - 在Google Analytics实时报告中查看是否有数据")


def verify_google_analytics_dashboard():
    """提供Google Analytics控制台验证说明"""
    print(f"\n📈 Google Analytics控制台验证:")
    print("-" * 40)
    print("1. 登录Google Analytics: https://analytics.google.com/")
    print("2. 选择对应的属性")
    print("3. 查看实时报告:")
    print("   - 左侧菜单 → 实时 → 概览")
    print("   - 应该能看到当前活跃用户")
    print("4. 查看事件:")
    print("   - 左侧菜单 → 实时 → 事件")
    print("   - 测试页面操作，查看事件是否记录")
    print("5. 验证数据流:")
    print("   - 管理 → 数据流 → 查看标记说明")
    print("   - 确认数据正常接收")


def check_configuration():
    """检查配置状态"""
    print(f"\n⚙️ 配置检查:")
    print("-" * 20)
    
    # 检查环境变量
    analytics_enabled = os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true'
    show_ui = os.getenv('SHOW_ANALYTICS_UI', 'false').lower() == 'true'
    tracking_id = os.getenv('GOOGLE_ANALYTICS_ID', '')
    
    print(f"ENABLE_ANALYTICS: {analytics_enabled} {'✅' if analytics_enabled else '❌'}")
    print(f"SHOW_ANALYTICS_UI: {show_ui} {'👁️' if show_ui else '🙈'}")
    print(f"GOOGLE_ANALYTICS_ID: {tracking_id if tracking_id else '未设置'} {'✅' if tracking_id else '❌'}")
    
    if not analytics_enabled:
        print("\n💡 启用统计:")
        print("在config.env中设置: ENABLE_ANALYTICS=true")
    
    if not tracking_id:
        print("\n💡 设置跟踪ID:")
        print("在config.env中设置: GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX")
    
    if analytics_enabled and tracking_id:
        print("\n✅ 配置正确！")
        return True
    else:
        print("\n❌ 配置不完整，请检查上述设置")
        return False


def main():
    """主函数"""
    print("🎯 Google Analytics验证工具")
    print("=" * 50)
    
    # 检查配置
    config_ok = check_configuration()
    
    if not config_ok:
        print("\n请先完成配置，然后重新运行此脚本")
        return
    
    # 验证代码注入
    injection_ok = verify_analytics_injection()
    
    # 提供验证说明
    verify_browser_instructions()
    verify_google_analytics_dashboard()
    
    # 总结
    print(f"\n" + "=" * 50)
    if injection_ok:
        print("🎉 验证完成！Google Analytics已正确配置")
        print("\n✅ 确认要点:")
        print("- 统计代码已注入到网页")
        print("- 配置参数正确")
        print("- 隐私设置已启用")
        
        print(f"\n📊 下一步:")
        print("1. 在浏览器中测试网站功能")
        print("2. 在Google Analytics中查看实时数据")
        print("3. 验证各种事件跟踪")
    else:
        print("❌ 验证失败！请检查配置和服务状态")
        
        print(f"\n🔧 故障排除:")
        print("1. 确认Web服务正在运行")
        print("2. 检查config.env配置")
        print("3. 重启Web服务")
        print("4. 查看服务器日志")


if __name__ == "__main__":
    main()
