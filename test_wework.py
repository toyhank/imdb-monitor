"""
企业微信机器人测试脚本
"""
import json
import requests
from config import Config, setup_logging
from notifier import Notifier

# 设置日志
logger = setup_logging()

def test_wework_format():
    """测试企业微信消息格式"""
    print("=== 测试企业微信消息格式 ===")
    
    # 创建测试数据
    test_data = {
        'message': 'IMDB Top 250 变化检测 - 测试数据',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '2部电影排名发生变化; 1部新电影进入榜单; 1部电影离开榜单',
            'rank_changes': [
                {
                    'title': 'The Godfather',
                    'old_rank': 2,
                    'new_rank': 1,
                    'change': '↑1',
                    'year': 1972,
                    'rating': 9.2
                },
                {
                    'title': 'The Shawshank Redemption',
                    'old_rank': 1,
                    'new_rank': 2,
                    'change': '↓1',
                    'year': 1994,
                    'rating': 9.3
                }
            ],
            'new_entries': [
                {
                    'title': 'Schindler\'s List',
                    'rank': 4,
                    'year': 1993,
                    'rating': 9.0
                }
            ],
            'removed_entries': [
                {
                    'title': '12 Angry Men',
                    'old_rank': 4,
                    'year': 1957,
                    'rating': 9.0
                }
            ]
        }
    }
    
    # 创建通知器
    notifier = Notifier()
    
    # 格式化企业微信消息
    wework_payload = notifier._format_wework_message(test_data)
    
    print("企业微信消息格式:")
    print(json.dumps(wework_payload, indent=2, ensure_ascii=False))
    
    print("\n消息内容预览:")
    print(wework_payload['markdown']['content'])
    
    return wework_payload

def test_slack_format():
    """测试Slack消息格式"""
    print("\n=== 测试Slack消息格式 ===")
    
    test_data = {
        'message': 'IMDB Top 250 变化检测 - 测试数据',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '2部电影排名发生变化; 1部新电影进入榜单',
            'rank_changes': [
                {
                    'title': 'The Godfather',
                    'old_rank': 2,
                    'new_rank': 1,
                    'change': '↑1'
                }
            ]
        }
    }
    
    notifier = Notifier()
    slack_payload = notifier._format_slack_message(test_data)
    
    print("Slack消息格式:")
    print(json.dumps(slack_payload, indent=2, ensure_ascii=False))
    
    return slack_payload

def test_send_to_wework():
    """测试发送到企业微信（需要配置真实的Webhook URL）"""
    print("\n=== 测试发送到企业微信 ===")
    
    if not Config.WEBHOOK_URL or 'your-webhook-url' in Config.WEBHOOK_URL:
        print("⚠️  请先在config.env中配置真实的企业微信Webhook URL")
        print("格式: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY")
        return False
    
    # 创建简单测试消息
    test_payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": """# 🧪 IMDB监控测试消息

**时间**: 2023-12-01 09:00:00
**状态**: 测试中

## 📋 测试项目
- ✅ 消息格式正确
- ✅ 网络连接正常
- ✅ 机器人配置成功

---
*这是一条测试消息，如果你看到这条消息，说明配置成功！*"""
        }
    }
    
    try:
        print(f"发送测试消息到: {Config.WEBHOOK_URL[:50]}...")
        
        response = requests.post(
            Config.WEBHOOK_URL,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        response.raise_for_status()
        
        result = response.json()
        if result.get('errcode') == 0:
            print("✅ 测试消息发送成功！")
            print("请检查企业微信群是否收到消息")
            return True
        else:
            print(f"❌ 发送失败: {result}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False

def test_full_notification():
    """测试完整的通知流程"""
    print("\n=== 测试完整通知流程 ===")
    
    # 创建完整的测试数据
    test_data = {
        'message': 'IMDB Top 250 变化检测 - 完整测试',
        'details': {
            'timestamp': '2023-12-01T09:00:00.123456',
            'summary': '3部电影排名发生变化; 2部新电影进入榜单; 1部电影离开榜单',
            'rank_changes': [
                {
                    'title': 'The Godfather',
                    'old_rank': 2,
                    'new_rank': 1,
                    'change': '↑1',
                    'year': 1972,
                    'rating': 9.2
                },
                {
                    'title': 'The Shawshank Redemption',
                    'old_rank': 1,
                    'new_rank': 2,
                    'change': '↓1',
                    'year': 1994,
                    'rating': 9.3
                },
                {
                    'title': 'The Dark Knight',
                    'old_rank': 4,
                    'new_rank': 3,
                    'change': '↑1',
                    'year': 2008,
                    'rating': 9.0
                }
            ],
            'new_entries': [
                {
                    'title': 'Schindler\'s List',
                    'rank': 5,
                    'year': 1993,
                    'rating': 9.0
                },
                {
                    'title': 'Pulp Fiction',
                    'rank': 6,
                    'year': 1994,
                    'rating': 8.9
                }
            ],
            'removed_entries': [
                {
                    'title': '12 Angry Men',
                    'old_rank': 5,
                    'year': 1957,
                    'rating': 9.0
                }
            ]
        }
    }
    
    # 测试通知器
    notifier = Notifier()
    
    print("发送完整测试通知...")
    success = notifier.send_notification(test_data)
    
    if success:
        print("✅ 完整通知测试成功！")
    else:
        print("❌ 完整通知测试失败")
    
    return success

def show_config_help():
    """显示配置帮助"""
    print("\n=== 配置帮助 ===")
    print("要使用企业微信机器人，请按以下步骤配置：")
    print()
    print("1. 在企业微信群中添加机器人")
    print("2. 获取Webhook URL")
    print("3. 编辑config.env文件：")
    print()
    print("WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY")
    print("NOTIFICATION_TYPE=webhook")
    print("WEBHOOK_TYPE=wework")
    print()
    print("详细配置指南请参考: WEWORK_SETUP.md")

def main():
    """主测试函数"""
    print("企业微信机器人测试脚本")
    print("=" * 40)
    
    # 测试消息格式
    test_wework_format()
    test_slack_format()
    
    # 显示配置信息
    print(f"\n当前配置:")
    print(f"  WEBHOOK_URL: {Config.WEBHOOK_URL[:50]}..." if Config.WEBHOOK_URL else "  WEBHOOK_URL: 未配置")
    print(f"  WEBHOOK_TYPE: {getattr(Config, 'WEBHOOK_TYPE', 'wework')}")
    print(f"  NOTIFICATION_TYPE: {Config.NOTIFICATION_TYPE}")
    
    # 测试发送
    if Config.WEBHOOK_URL and 'your-webhook-url' not in Config.WEBHOOK_URL:
        test_send_to_wework()
        test_full_notification()
    else:
        show_config_help()

if __name__ == "__main__":
    main()
