#!/usr/bin/env python3
"""
Google Analytics功能测试脚本
用于测试Google Analytics统计功能是否正常工作
"""

import requests
import time
import os
from google_analytics import google_analytics


def test_google_analytics_config():
    """测试Google Analytics配置"""
    print("🧪 测试Google Analytics配置...")
    
    # 测试配置状态
    print("\n1. 检查配置状态...")
    status = google_analytics.get_config_status()
    print(f"   启用状态: {status['enabled']}")
    print(f"   跟踪ID: {status.get('tracking_id', '未配置')}")
    
    if status['enabled']:
        print("   ✅ Google Analytics已启用")
        print("   启用的功能:")
        for feature, enabled in status['features'].items():
            print(f"      - {feature}: {'✅' if enabled else '❌'}")
    else:
        print("   ⚠️  Google Analytics未启用")
        print("   请在config.env中设置:")
        print("      ENABLE_ANALYTICS=true")
        print("      GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX")
    
    return status['enabled']


def test_tracking_script():
    """测试跟踪脚本生成"""
    print("\n2. 测试跟踪脚本生成...")
    
    script = google_analytics.get_tracking_script()
    
    if script:
        print(f"   ✅ 脚本生成成功，长度: {len(script)} 字符")
        
        # 检查脚本内容
        if 'gtag' in script:
            print("   ✅ 包含gtag函数")
        if 'anonymize_ip' in script:
            print("   ✅ 包含IP匿名化设置")
        if 'external_link' in script:
            print("   ✅ 包含外部链接跟踪")
        if 'file_download' in script:
            print("   ✅ 包含文件下载跟踪")
        
        print(f"   📄 脚本预览: {script[:200]}...")
    else:
        print("   ❌ 脚本生成失败或为空")
    
    return bool(script)


def test_web_api():
    """测试Web API接口"""
    print("\n3. 测试Web API接口...")
    
    base_url = "http://localhost:5000"
    
    try:
        # 测试统计脚本API
        print("   测试 /api/analytics/scripts...")
        response = requests.get(f"{base_url}/api/analytics/scripts", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API响应成功")
            print(f"   启用状态: {data.get('enabled', False)}")
            
            if data.get('scripts'):
                print(f"   ✅ 脚本内容长度: {len(data['scripts'])} 字符")
            else:
                print("   ⚠️  脚本内容为空")
        else:
            print(f"   ❌ API响应失败: {response.status_code}")
        
        # 测试统计状态API
        print("   测试 /api/analytics/status...")
        response = requests.get(f"{base_url}/api/analytics/status", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 状态API响应成功")
            print(f"   配置状态: {data}")
        else:
            print(f"   ❌ 状态API响应失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ 无法连接到Web服务器")
        print("   请确保Web服务器正在运行: python main.py --web")
    except Exception as e:
        print(f"   ❌ API测试失败: {e}")


def test_web_interface():
    """测试Web界面集成"""
    print("\n4. 测试Web界面集成...")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(base_url, timeout=5)
        
        if response.status_code == 200:
            content = response.text
            
            # 检查是否包含统计相关元素
            if "analytics-status" in content:
                # 检查是否被隐藏
                if 'style="display: none;"' in content and 'analytics-card' in content:
                    print("   ✅ Web界面包含统计状态区域 (已隐藏)")
                else:
                    print("   ✅ Web界面包含统计状态区域 (显示)")
            else:
                print("   ❌ Web界面缺少统计状态区域")
            
            if "loadAnalyticsStatus" in content:
                print("   ✅ Web界面包含统计状态加载代码")
            else:
                print("   ❌ Web界面缺少统计状态加载代码")
            
            if "loadAnalyticsScripts" in content:
                print("   ✅ Web界面包含统计脚本加载代码")
            else:
                print("   ❌ Web界面缺少统计脚本加载代码")
            
            print(f"   ✅ Web界面访问成功，页面大小: {len(content)} 字符")
        else:
            print(f"   ❌ Web界面访问失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ 无法连接到Web服务器")
    except Exception as e:
        print(f"   ❌ Web界面测试失败: {e}")


def simulate_user_activity():
    """模拟用户活动"""
    print("\n5. 模拟用户活动...")
    
    base_url = "http://localhost:5000"
    
    try:
        # 模拟页面访问
        print("   模拟页面访问...")
        for i in range(3):
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ 访问 {i+1}: 成功")
            else:
                print(f"   ❌ 访问 {i+1}: 失败 ({response.status_code})")
            time.sleep(1)
        
        # 模拟API调用
        print("   模拟API调用...")
        api_endpoints = [
            "/api/movies",
            "/api/analytics/status",
            "/api/analytics/scripts"
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                print(f"   ✅ {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint}: 失败 ({e})")
        
        print("   📊 模拟活动完成，请检查Google Analytics是否记录了这些访问")
        
    except Exception as e:
        print(f"   ❌ 模拟活动失败: {e}")


def check_environment():
    """检查环境配置"""
    print("\n6. 检查环境配置...")

    # 检查环境变量
    analytics_enabled = os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true'
    show_analytics_ui = os.getenv('SHOW_ANALYTICS_UI', 'false').lower() == 'true'
    analytics_id = os.getenv('GOOGLE_ANALYTICS_ID', '')

    print(f"   ENABLE_ANALYTICS: {analytics_enabled}")
    print(f"   SHOW_ANALYTICS_UI: {show_analytics_ui}")
    print(f"   GOOGLE_ANALYTICS_ID: {analytics_id if analytics_id else '未设置'}")
    
    # 检查配置文件
    config_files = ['config.env', 'config.env.example']
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   ✅ {config_file} 存在")
            
            # 读取配置文件内容
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'GOOGLE_ANALYTICS_ID' in content:
                    print(f"   ✅ {config_file} 包含Google Analytics配置")
                else:
                    print(f"   ⚠️  {config_file} 缺少Google Analytics配置")
        else:
            print(f"   ❌ {config_file} 不存在")


def main():
    """主测试函数"""
    print("🎯 IMDB监控系统 - Google Analytics功能测试")
    print("=" * 60)
    
    # 检查环境配置
    check_environment()
    
    # 测试Google Analytics配置
    is_enabled = test_google_analytics_config()
    
    # 测试跟踪脚本生成
    script_ok = test_tracking_script()
    
    # 等待Web服务器启动
    print("\n⏳ 等待Web服务器启动...")
    time.sleep(2)
    
    # 测试Web API
    test_web_api()
    
    # 测试Web界面
    test_web_interface()
    
    # 模拟用户活动
    simulate_user_activity()
    
    # 显示测试总结
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("\n📋 测试总结:")
    
    if is_enabled:
        print("✅ Google Analytics配置正确")
    else:
        print("❌ Google Analytics未启用")
    
    if script_ok:
        print("✅ 跟踪脚本生成正常")
    else:
        print("❌ 跟踪脚本生成失败")
    
    print("\n💡 下一步:")
    if not is_enabled:
        print("1. 在config.env中配置Google Analytics")
        print("   ENABLE_ANALYTICS=true")
        print("   GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX")
        print("2. 重启Web服务")
    else:
        print("1. 访问 http://localhost:5000 查看Web界面")
        print("2. 在Google Analytics中查看实时数据")
        print("3. 测试各种用户操作（搜索、导出等）")
    
    print("\n📚 参考文档:")
    print("- GOOGLE_ANALYTICS_SETUP.md - 详细设置指南")
    print("- config.env.example - 配置文件示例")


if __name__ == "__main__":
    main()
