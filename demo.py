"""
演示脚本 - 用于测试和演示IMDB监控功能
"""
import json
import logging
from config import setup_logging
from database import DatabaseManager
from scraper import IMDBScraper
from change_detector import ChangeDetector
from notifier import Notifier

# 设置日志
logger = setup_logging()

def demo_scraping():
    """演示爬取功能"""
    print("=== 演示IMDB Top 250爬取功能 ===")
    
    scraper = IMDBScraper()
    movies = scraper.fetch_top250()
    
    if movies:
        print(f"成功爬取 {len(movies)} 部电影")
        print("\n前5部电影:")
        for i, movie in enumerate(movies[:5], 1):
            print(f"{i}. {movie['title']} ({movie.get('year', 'N/A')}) - 评分: {movie.get('rating', 'N/A')}")
        
        # 验证数据
        is_valid = scraper.validate_data(movies)
        print(f"\n数据验证: {'通过' if is_valid else '失败'}")
        
        return movies
    else:
        print("爬取失败")
        return []

def demo_database():
    """演示数据库功能"""
    print("\n=== 演示数据库功能 ===")
    
    db = DatabaseManager("demo.db")
    
    # 创建测试数据
    test_movies = [
        {
            'imdb_id': 'tt0111161',
            'title': 'The Shawshank Redemption',
            'year': 1994,
            'rating': 9.3,
            'rank': 1
        },
        {
            'imdb_id': 'tt0068646',
            'title': 'The Godfather',
            'year': 1972,
            'rating': 9.2,
            'rank': 2
        },
        {
            'imdb_id': 'tt0468569',
            'title': 'The Dark Knight',
            'year': 2008,
            'rating': 9.0,
            'rank': 3
        }
    ]
    
    # 保存数据
    success = db.save_current_top250(test_movies)
    print(f"保存数据: {'成功' if success else '失败'}")
    
    # 获取数据
    retrieved = db.get_latest_data()
    print(f"获取数据: {len(retrieved)} 条记录")
    
    # 保存快照
    success = db.save_snapshot(test_movies)
    print(f"保存快照: {'成功' if success else '失败'}")
    
    return test_movies

def demo_change_detection():
    """演示变化检测功能"""
    print("\n=== 演示变化检测功能 ===")
    
    detector = ChangeDetector()
    
    # 旧数据
    old_data = [
        {'imdb_id': 'tt0111161', 'title': 'The Shawshank Redemption', 'rank': 1, 'rating': 9.3},
        {'imdb_id': 'tt0068646', 'title': 'The Godfather', 'rank': 2, 'rating': 9.2},
        {'imdb_id': 'tt0468569', 'title': 'The Dark Knight', 'rank': 3, 'rating': 9.0},
        {'imdb_id': 'tt0050083', 'title': '12 Angry Men', 'rank': 4, 'rating': 9.0}
    ]
    
    # 新数据（模拟变化）
    new_data = [
        {'imdb_id': 'tt0068646', 'title': 'The Godfather', 'rank': 1, 'rating': 9.2},  # 上升
        {'imdb_id': 'tt0111161', 'title': 'The Shawshank Redemption', 'rank': 2, 'rating': 9.3},  # 下降
        {'imdb_id': 'tt0468569', 'title': 'The Dark Knight', 'rank': 3, 'rating': 9.0},  # 不变
        {'imdb_id': 'tt0108052', 'title': 'Schindler\'s List', 'rank': 4, 'rating': 9.0}  # 新增
        # tt0050083 被移除
    ]
    
    # 检测变化
    changes = detector.detect_changes(old_data, new_data)
    
    print(f"检测到变化: {'是' if changes['has_changes'] else '否'}")
    print(f"摘要: {changes['summary']}")
    
    if changes['rank_changes']:
        print(f"\n排名变化 ({len(changes['rank_changes'])} 个):")
        for change in changes['rank_changes']:
            direction = "↑" if change['rank_diff'] > 0 else "↓"
            print(f"  • {change['title']}: #{change['old_rank']} → #{change['new_rank']} ({direction}{abs(change['rank_diff'])})")
    
    if changes['new_entries']:
        print(f"\n新增电影 ({len(changes['new_entries'])} 个):")
        for entry in changes['new_entries']:
            print(f"  • {entry['title']}: #{entry['new_rank']}")
    
    if changes['removed_entries']:
        print(f"\n移除电影 ({len(changes['removed_entries'])} 个):")
        for entry in changes['removed_entries']:
            print(f"  • {entry['title']}: 原#{entry['old_rank']}")
    
    # 格式化通知数据
    notification_data = detector.format_changes_for_notification(changes)
    print(f"\n通知消息: {notification_data['message']}")

    # 演示企业微信消息格式
    if changes['has_changes']:
        print("\n--- 企业微信消息格式预览 ---")
        notifier = Notifier()
        wework_messages = notifier._format_wework_messages(notification_data)

        for i, message in enumerate(wework_messages, 1):
            print(f"\n消息 {i} ({message['msgtype']}):")

            if message['msgtype'] == 'news':
                articles = message['news']['articles']
                print(f"  📰 图文消息 - {len(articles)} 个文章")
                for j, article in enumerate(articles):
                    print(f"    {j+1}. {article['title']}")
                    print(f"       {article['description'][:50]}...")
                    if article['picurl']:
                        print(f"       🖼️ 包含图片")
            elif message['msgtype'] == 'markdown':
                content = message['markdown']['content']
                print(f"  📝 Markdown消息:")
                print(content[:200] + "..." if len(content) > 200 else content)

    return changes

def demo_notification():
    """演示通知功能"""
    print("\n=== 演示通知功能 ===")

    # 创建模拟通知数据
    notification_data = {
        'message': 'IMDB Top 250 变化检测 - 演示数据',
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

    print("通知数据预览:")
    print(json.dumps(notification_data, indent=2, ensure_ascii=False))

    # 演示不同平台的消息格式
    demo_message_formats(notification_data)

    # 演示图文消息功能
    demo_news_message_feature(notification_data)

    # 测试实际发送
    demo_send_test(notification_data)

def demo_message_formats(notification_data):
    """演示不同平台的消息格式"""
    print("\n--- 不同平台消息格式对比 ---")

    notifier = Notifier()

    # 企业微信格式
    print("\n🔸 企业微信机器人格式:")
    wework_msg = notifier._format_wework_message(notification_data)
    print(wework_msg['markdown']['content'])

    # Slack格式
    print("\n🔸 Slack机器人格式:")
    slack_msg = notifier._format_slack_message(notification_data)
    print("消息块数量:", len(slack_msg['blocks']))
    print("标题:", slack_msg['blocks'][0]['text']['text'])

    # 通用格式
    print("\n🔸 通用Webhook格式:")
    generic_msg = notifier._format_generic_message(notification_data)
    print(f"消息: {generic_msg['text']}")
    print(f"摘要: {generic_msg['summary']}")

def demo_news_message_feature(notification_data):
    """演示图文消息功能"""
    print("\n🔸 企业微信图文消息功能:")

    notifier = Notifier()
    details = notification_data.get('details', {})

    # 检查是否有新增或下架电影
    has_new_or_removed = (details.get('new_entries') or details.get('removed_entries'))

    if has_new_or_removed:
        print("   ✅ 检测到新增或下架电影")
        print("   📰 将生成图文消息（news类型）")
        print("   🖼️ 新增电影包含海报图片")
        print("   🔗 支持点击跳转到IMDB")

        # 演示图文消息结构
        print("\n   图文消息结构:")
        print("   ├─ 主文章: 🎬 IMDB Top 250 榜单更新")
        print("   │  ├─ 标题: 榜单更新通知")
        print("   │  ├─ 描述: 时间和摘要信息")
        print("   │  ├─ 图片: 新增电影的海报（如有）")
        print("   │  └─ 链接: https://www.imdb.com/chart/top/")

        if details.get('new_entries'):
            print("   ├─ 新增电影文章:")
            for i, entry in enumerate(details['new_entries'][:3], 1):
                print(f"   │  └─ 🆕 {entry.get('title', 'Unknown')} (#{entry.get('rank', 'N/A')})")

        if details.get('removed_entries'):
            print("   └─ 下架电影文章:")
            for i, entry in enumerate(details['removed_entries'][:2], 1):
                print(f"      └─ 📤 {entry.get('title', 'Unknown')} (原#{entry.get('old_rank', 'N/A')})")
    else:
        print("   ℹ️ 只有排名变化，无新增/下架电影")
        print("   📝 将使用普通Markdown消息")
        print("   💡 图文消息仅在有新增或下架电影时发送")

def demo_send_test(notification_data):
    """演示发送测试"""
    print("\n--- 发送测试 ---")

    from config import Config

    # 显示当前配置
    print(f"当前配置:")
    print(f"  WEBHOOK_URL: {Config.WEBHOOK_URL[:50]}..." if Config.WEBHOOK_URL else "  WEBHOOK_URL: 未配置")
    print(f"  WEBHOOK_TYPE: {getattr(Config, 'WEBHOOK_TYPE', 'wework')}")
    print(f"  NOTIFICATION_TYPE: {Config.NOTIFICATION_TYPE}")

    # 如果配置了真实的webhook URL，提供发送选项
    if Config.WEBHOOK_URL and 'your-webhook-url' not in Config.WEBHOOK_URL and 'YOUR_KEY' not in Config.WEBHOOK_URL:
        print("\n检测到已配置的Webhook URL")
        try:
            user_input = input("是否发送测试消息到企业微信群? (y/N): ").strip().lower()
            if user_input == 'y':
                notifier = Notifier()
                success = notifier.send_notification(notification_data)
                if success:
                    print("✅ 测试消息发送成功！请检查企业微信群")
                else:
                    print("❌ 测试消息发送失败，请检查配置和日志")
            else:
                print("跳过发送测试")
        except KeyboardInterrupt:
            print("\n跳过发送测试")
    else:
        print("\n💡 配置说明:")
        print("要测试实际发送，请按以下步骤配置:")
        print("1. 在企业微信群中添加机器人")
        print("2. 获取Webhook URL")
        print("3. 编辑config.env文件:")
        print("   WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY")
        print("   WEBHOOK_TYPE=wework")
        print("4. 运行: python test_wework.py")
        print("\n📖 详细配置指南: WEWORK_SETUP.md")

def main():
    """主演示函数"""
    print("IMDB Top 250 监控系统演示")
    print("=" * 50)
    
    try:
        # 演示各个模块
        movies = demo_scraping()
        demo_database()
        demo_change_detection()
        demo_notification()
        
        print("\n=== 演示完成 ===")
        print("要运行完整的监控程序，请执行: python main.py")
        print("要执行一次性检查，请执行: python main.py --once")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
