"""
使用模拟数据演示图文消息功能
"""
import json
from config import setup_logging
from change_detector import ChangeDetector
from notifier import Notifier

# 设置日志
logger = setup_logging()

def create_mock_old_data():
    """创建模拟的旧数据"""
    return [
        {'imdb_id': 'tt0111161', 'title': 'The Shawshank Redemption', 'rank': 1, 'year': 1994, 'rating': 9.3},
        {'imdb_id': 'tt0068646', 'title': 'The Godfather', 'rank': 2, 'year': 1972, 'rating': 9.2},
        {'imdb_id': 'tt0468569', 'title': 'The Dark Knight', 'rank': 3, 'year': 2008, 'rating': 9.0},
        {'imdb_id': 'tt0050083', 'title': '12 Angry Men', 'rank': 4, 'year': 1957, 'rating': 9.0},
        {'imdb_id': 'tt0108052', 'title': 'Schindler\'s List', 'rank': 5, 'year': 1993, 'rating': 9.0},
        {'imdb_id': 'tt0118799', 'title': 'Life Is Beautiful', 'rank': 249, 'year': 1997, 'rating': 8.6},
        {'imdb_id': 'tt0110912', 'title': 'Pulp Fiction', 'rank': 250, 'year': 1994, 'rating': 8.9},
    ]

def create_mock_new_data():
    """创建模拟的新数据（包含新增和下架）"""
    return [
        {'imdb_id': 'tt0111161', 'title': 'The Shawshank Redemption', 'rank': 2, 'year': 1994, 'rating': 9.3},  # 下降
        {'imdb_id': 'tt0068646', 'title': 'The Godfather', 'rank': 1, 'year': 1972, 'rating': 9.2},  # 上升
        {'imdb_id': 'tt0468569', 'title': 'The Dark Knight', 'rank': 3, 'year': 2008, 'rating': 9.0},  # 不变
        {'imdb_id': 'tt0050083', 'title': '12 Angry Men', 'rank': 4, 'year': 1957, 'rating': 9.0},  # 不变
        {'imdb_id': 'tt0108052', 'title': 'Schindler\'s List', 'rank': 5, 'year': 1993, 'rating': 9.0},  # 不变
        # 新增电影
        {'imdb_id': 'tt15398776', 'title': 'Oppenheimer', 'rank': 15, 'year': 2023, 'rating': 8.8},
        {'imdb_id': 'tt6710474', 'title': 'Everything Everywhere All at Once', 'rank': 45, 'year': 2022, 'rating': 8.1},
        # Life Is Beautiful 和 Pulp Fiction 被移除
        {'imdb_id': 'tt0167260', 'title': 'The Lord of the Rings: The Return of the King', 'rank': 249, 'year': 2003, 'rating': 8.9},
        {'imdb_id': 'tt0120737', 'title': 'The Lord of the Rings: The Fellowship of the Ring', 'rank': 250, 'year': 2001, 'rating': 8.8},
    ]

def demo_change_detection():
    """演示变化检测"""
    print("=== 演示变化检测功能 ===")
    
    old_data = create_mock_old_data()
    new_data = create_mock_new_data()
    
    print(f"旧数据: {len(old_data)} 部电影")
    print(f"新数据: {len(new_data)} 部电影")
    
    detector = ChangeDetector()
    changes = detector.detect_changes(old_data, new_data)
    
    print(f"\n检测结果:")
    print(f"  有变化: {changes['has_changes']}")
    print(f"  摘要: {changes['summary']}")
    print(f"  排名变化: {len(changes['rank_changes'])} 个")
    print(f"  新增电影: {len(changes['new_entries'])} 个")
    print(f"  移除电影: {len(changes['removed_entries'])} 个")
    
    if changes['new_entries']:
        print(f"\n新增电影:")
        for entry in changes['new_entries']:
            print(f"  - {entry['title']} (#{entry['new_rank']})")
    
    if changes['removed_entries']:
        print(f"\n移除电影:")
        for entry in changes['removed_entries']:
            print(f"  - {entry['title']} (原#{entry['old_rank']})")
    
    return changes

def demo_notification_formatting():
    """演示通知格式化"""
    print("\n=== 演示通知格式化 ===")
    
    # 获取变化数据
    old_data = create_mock_old_data()
    new_data = create_mock_new_data()
    detector = ChangeDetector()
    changes = detector.detect_changes(old_data, new_data)
    
    # 格式化通知数据
    notification_data = detector.format_changes_for_notification(changes)
    
    print(f"通知消息: {notification_data['message']}")
    
    # 演示企业微信消息格式
    notifier = Notifier()
    messages = notifier._format_wework_messages(notification_data)
    
    print(f"\n生成了 {len(messages)} 条企业微信消息:")
    
    for i, message in enumerate(messages, 1):
        print(f"\n消息 {i}:")
        print(f"  类型: {message['msgtype']}")
        
        if message['msgtype'] == 'news':
            articles = message['news']['articles']
            print(f"  📰 图文消息 - {len(articles)} 个文章")
            
            for j, article in enumerate(articles, 1):
                print(f"    文章 {j}: {article['title']}")
                print(f"      描述: {article['description'][:50]}...")
                print(f"      链接: {article['url']}")
                if article['picurl']:
                    print(f"      图片: 有")
                else:
                    print(f"      图片: 无")
        
        elif message['msgtype'] == 'markdown':
            content = message['markdown']['content']
            print(f"  📝 Markdown消息:")
            print(f"      长度: {len(content)} 字符")
            print(f"      预览: {content[:100]}...")
    
    return messages

def demo_json_output():
    """演示JSON输出"""
    print("\n=== 演示JSON输出 ===")
    
    # 获取变化数据
    old_data = create_mock_old_data()
    new_data = create_mock_new_data()
    detector = ChangeDetector()
    changes = detector.detect_changes(old_data, new_data)
    notification_data = detector.format_changes_for_notification(changes)
    
    # 生成企业微信消息
    notifier = Notifier()
    messages = notifier._format_wework_messages(notification_data)
    
    print("企业微信图文消息JSON格式:")
    for i, message in enumerate(messages, 1):
        print(f"\n--- 消息 {i} ---")
        print(json.dumps(message, indent=2, ensure_ascii=False))

def demo_send_test():
    """演示发送测试"""
    print("\n=== 演示发送测试 ===")
    
    from config import Config
    
    if not Config.WEBHOOK_URL or 'YOUR_KEY' in Config.WEBHOOK_URL:
        print("⚠️  请先配置真实的企业微信Webhook URL")
        print("配置方法:")
        print("1. 在企业微信群中添加机器人")
        print("2. 获取Webhook URL")
        print("3. 编辑config.env文件中的WEBHOOK_URL")
        return False
    
    # 创建测试数据
    old_data = create_mock_old_data()
    new_data = create_mock_new_data()
    detector = ChangeDetector()
    changes = detector.detect_changes(old_data, new_data)
    notification_data = detector.format_changes_for_notification(changes)
    
    try:
        user_input = input("是否发送模拟的图文消息到企业微信群? (y/N): ").strip().lower()
        if user_input == 'y':
            print("发送模拟图文消息...")
            
            notifier = Notifier()
            success = notifier.send_notification(notification_data)
            
            if success:
                print("✅ 模拟图文消息发送成功！")
                print("请检查企业微信群是否收到包含以下内容的消息:")
                print("  📰 图文消息格式")
                print("  🆕 新增电影: Oppenheimer, Everything Everywhere All at Once")
                print("  📤 移除电影: Life Is Beautiful, Pulp Fiction")
                print("  🖼️ 电影海报图片")
                print("  🔗 可点击的IMDB链接")
            else:
                print("❌ 图文消息发送失败")
            
            return success
        else:
            print("跳过发送测试")
            return True
    except KeyboardInterrupt:
        print("\n跳过发送测试")
        return True

def show_feature_summary():
    """显示功能总结"""
    print("\n=== 功能总结 ===")
    print("🎉 图文消息功能已完成集成！")
    print()
    print("✅ 智能消息类型选择:")
    print("   - 有新增/下架电影 → 图文消息")
    print("   - 只有排名变化 → Markdown消息")
    print()
    print("✅ 图文消息特性:")
    print("   - 🖼️ 包含电影海报图片")
    print("   - 📋 详细的排名和电影信息")
    print("   - 🔗 可点击跳转到IMDB页面")
    print("   - 📱 在企业微信中显示为卡片样式")
    print()
    print("✅ 支持的变化类型:")
    print("   - 🆕 新增电影进入榜单")
    print("   - 📤 电影离开榜单")
    print("   - 📊 电影排名变化")
    print()
    print("🔧 配置要求:")
    print("   - ENABLE_MOVIE_IMAGES=true")
    print("   - WEBHOOK_TYPE=wework")
    print("   - NOTIFICATION_TYPE=webhook")

def main():
    """主演示函数"""
    print("IMDB Top 250 图文消息功能完整演示")
    print("=" * 60)
    print("注意: 由于IMDB反爬虫限制，本演示使用模拟数据")
    print("=" * 60)
    
    try:
        # 演示各个功能
        changes = demo_change_detection()
        messages = demo_notification_formatting()
        demo_json_output()
        demo_send_test()
        show_feature_summary()
        
        print("\n" + "=" * 60)
        print("演示完成！图文消息功能已准备就绪。")
        print("当IMDB访问恢复正常时，程序将自动使用图文消息功能。")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
