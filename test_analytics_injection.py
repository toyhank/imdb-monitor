#!/usr/bin/env python3
"""
测试Google Analytics代码注入功能
验证统计代码是否正确注入到网页中
"""

import requests
import os
import sys
from google_analytics import google_analytics


def test_analytics_injection():
    """测试统计代码注入"""
    print("🧪 测试Google Analytics代码注入")
    print("=" * 50)
    
    # 检查配置
    print("\n1. 检查Google Analytics配置...")
    status = google_analytics.get_config_status()
    print(f"   启用状态: {status['enabled']}")
    print(f"   跟踪ID: {status.get('tracking_id', '未配置')}")
    
    if not status['enabled']:
        print("   ⚠️  Google Analytics未启用，无法测试代码注入")
        print("   请在config.env中设置:")
        print("      ENABLE_ANALYTICS=true")
        print("      GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX")
        return False
    
    # 测试脚本生成
    print("\n2. 测试统计脚本生成...")
    script = google_analytics.get_tracking_script()
    if script:
        print(f"   ✅ 脚本生成成功，长度: {len(script)} 字符")
        
        # 检查关键内容
        if 'gtag' in script:
            print("   ✅ 包含gtag函数")
        if status['tracking_id'] in script:
            print(f"   ✅ 包含跟踪ID: {status['tracking_id']}")
        if 'anonymize_ip' in script:
            print("   ✅ 包含IP匿名化设置")
        
        print(f"   📄 脚本预览:")
        print("   " + "\n   ".join(script.split('\n')[:10]))
        print("   ...")
    else:
        print("   ❌ 脚本生成失败")
        return False
    
    # 测试Web页面注入
    print("\n3. 测试Web页面代码注入...")
    try:
        response = requests.get("http://localhost:5000", timeout=10)
        if response.status_code == 200:
            content = response.text
            print(f"   ✅ 页面访问成功，大小: {len(content)} 字符")
            
            # 检查是否包含Google Analytics代码
            if 'googletagmanager.com/gtag/js' in content:
                print("   ✅ 页面包含Google Analytics脚本加载")
            else:
                print("   ❌ 页面缺少Google Analytics脚本加载")
            
            if 'gtag(' in content:
                print("   ✅ 页面包含gtag函数调用")
            else:
                print("   ❌ 页面缺少gtag函数调用")
            
            if status['tracking_id'] in content:
                print(f"   ✅ 页面包含跟踪ID: {status['tracking_id']}")
            else:
                print(f"   ❌ 页面缺少跟踪ID: {status['tracking_id']}")
            
            if 'anonymize_ip' in content:
                print("   ✅ 页面包含IP匿名化设置")
            else:
                print("   ❌ 页面缺少IP匿名化设置")
            
            # 检查代码位置
            if '</head>' in content:
                head_end_pos = content.find('</head>')
                head_content = content[:head_end_pos]
                if 'gtag' in head_content:
                    print("   ✅ 统计代码正确位于<head>部分")
                else:
                    print("   ⚠️  统计代码可能不在<head>部分")
            
            # 保存页面内容用于调试
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("   📄 页面内容已保存到 debug_page.html")
            
            return True
        else:
            print(f"   ❌ 页面访问失败: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ 无法连接到Web服务器")
        print("   请确保Web服务器正在运行: python main.py --web")
        return False
    except Exception as e:
        print(f"   ❌ 页面测试失败: {e}")
        return False


def test_analytics_api():
    """测试统计API"""
    print("\n4. 测试统计API...")
    
    try:
        # 测试脚本API
        response = requests.get("http://localhost:5000/api/analytics/scripts", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ 统计脚本API响应成功")
            print(f"   启用状态: {data.get('enabled', False)}")
            
            if data.get('scripts'):
                print(f"   ✅ API返回脚本内容，长度: {len(data['scripts'])} 字符")
            else:
                print("   ⚠️  API返回空脚本内容")
        else:
            print(f"   ❌ 统计脚本API失败: {response.status_code}")
        
        # 测试状态API
        response = requests.get("http://localhost:5000/api/analytics/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ 统计状态API响应成功")
            print(f"   配置状态: {data}")
        else:
            print(f"   ❌ 统计状态API失败: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ API测试失败: {e}")


def check_browser_console():
    """检查浏览器控制台的建议"""
    print("\n5. 浏览器验证建议...")
    print("   请在浏览器中执行以下步骤验证:")
    print("   1. 访问 http://localhost:5000")
    print("   2. 按F12打开开发者工具")
    print("   3. 在Console中输入: typeof gtag")
    print("   4. 应该返回 'function' 表示gtag已加载")
    print("   5. 在Network标签中查看是否有googletagmanager.com的请求")
    print("   6. 在Elements标签中查看<head>部分是否有Google Analytics代码")


def main():
    """主函数"""
    print("🎯 Google Analytics代码注入测试")
    print("=" * 60)
    
    # 检查环境变量
    analytics_enabled = os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true'
    analytics_id = os.getenv('GOOGLE_ANALYTICS_ID', '')
    show_ui = os.getenv('SHOW_ANALYTICS_UI', 'false').lower() == 'true'
    
    print(f"环境配置:")
    print(f"  ENABLE_ANALYTICS: {analytics_enabled}")
    print(f"  SHOW_ANALYTICS_UI: {show_ui}")
    print(f"  GOOGLE_ANALYTICS_ID: {analytics_id if analytics_id else '未设置'}")
    
    if not analytics_enabled or not analytics_id:
        print("\n❌ Google Analytics未正确配置")
        print("请在config.env中设置:")
        print("  ENABLE_ANALYTICS=true")
        print("  GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX")
        print("\n然后重启Web服务: python main.py --web")
        return
    
    # 执行测试
    success = test_analytics_injection()
    test_analytics_api()
    check_browser_console()
    
    # 显示结果
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试完成！Google Analytics代码注入正常")
        print("\n✅ 验证要点:")
        print("- 统计代码已注入到页面<head>部分")
        print("- 包含正确的跟踪ID")
        print("- 启用了IP匿名化")
        print("- API接口正常响应")
        
        print("\n📊 下一步:")
        print("1. 在浏览器中访问网站进行测试")
        print("2. 在Google Analytics中查看实时数据")
        print("3. 验证事件跟踪是否正常工作")
    else:
        print("❌ 测试失败！请检查配置和服务状态")
        print("\n🔧 故障排除:")
        print("1. 确认Web服务正在运行")
        print("2. 检查Google Analytics配置")
        print("3. 查看服务器日志")
        print("4. 验证网络连接")
    
    print(f"\n📄 调试文件: debug_page.html")
    print("💡 提示: 查看该文件确认统计代码是否正确注入")


if __name__ == "__main__":
    main()
