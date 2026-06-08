"""
演示新增/下架电影图文消息功能
"""
import json
from config import setup_logging
from notifier import Notifier

# 设置日志
logger = setup_logging()

def demo_message_logic():
    """演示消息逻辑"""
    print("企业微信图文消息逻辑演示")
    print("=" * 50)
    
    print("\n📋 消息发送逻辑:")
    print("✅ 有新增或下架电影 → 发送图文消息（news类型）")
    print("✅ 只有排名变化 → 发送Markdown消息")
    print("✅ 图文消息包含电影海报和详细信息")
    print("✅ 支持点击跳转到IMDB页面")

def demo_new_movies_scenario():
    """演示新增电影场景"""
    print("\n=== 场景1: 新增电影进入榜单 ===")
    
    test_data = {
        'message': 'IMDB Top 250 新增电影',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '2部新电影进入榜单',
            'new_entries': [
                {
                    'imdb_id': 'tt15398776',
                    'title': 'Oppenheimer',
                    'rank': 15,
                    'year': 2023,
                    'rating': 8.8
                },
                {
                    'imdb_id': 'tt6710474',
                    'title': 'Everything Everywhere All at Once',
                    'rank': 45,
                    'year': 2022,
                    'rating': 8.1
                }
            ]
        }
    }
    
    notifier = Notifier()
    messages = notifier._format_wework_messages(test_data)
    
    print(f"📰 生成图文消息: {len(messages)} 条")
    
    for message in messages:
        if message['msgtype'] == 'news':
            articles = message['news']['articles']
            print(f"\n图文消息包含 {len(articles)} 个文章:")
            
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article['title']}")
                print(f"     📝 {article['description'].split()[0]}...")
                print(f"     🔗 {article['url']}")
                if article['picurl']:
                    print(f"     🖼️ 包含海报图片")

def demo_removed_movies_scenario():
    """演示下架电影场景"""
    print("\n=== 场景2: 电影离开榜单 ===")
    
    test_data = {
        'message': 'IMDB Top 250 电影下架',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '1部电影离开榜单',
            'removed_entries': [
                {
                    'imdb_id': 'tt0118799',
                    'title': 'Life Is Beautiful',
                    'old_rank': 249,
                    'year': 1997,
                    'rating': 8.6
                }
            ]
        }
    }
    
    notifier = Notifier()
    messages = notifier._format_wework_messages(test_data)
    
    print(f"📰 生成图文消息: {len(messages)} 条")
    
    for message in messages:
        if message['msgtype'] == 'news':
            articles = message['news']['articles']
            print(f"\n图文消息包含 {len(articles)} 个文章:")
            
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article['title']}")
                print(f"     📝 {article['description'].split()[0]}...")

def demo_rank_changes_scenario():
    """演示排名变化场景"""
    print("\n=== 场景3: 只有排名变化 ===")
    
    test_data = {
        'message': 'IMDB Top 250 排名变化',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '3部电影排名发生变化',
            'rank_changes': [
                {
                    'imdb_id': 'tt0111161',
                    'title': 'The Shawshank Redemption',
                    'old_rank': 2,
                    'new_rank': 1,
                    'change': '↑1'
                },
                {
                    'imdb_id': 'tt0068646',
                    'title': 'The Godfather',
                    'old_rank': 1,
                    'new_rank': 2,
                    'change': '↓1'
                }
            ]
        }
    }
    
    notifier = Notifier()
    messages = notifier._format_wework_messages(test_data)
    
    print(f"📝 生成Markdown消息: {len(messages)} 条")
    
    for message in messages:
        if message['msgtype'] == 'markdown':
            content = message['markdown']['content']
            print(f"\nMarkdown消息内容:")
            print(content[:200] + "..." if len(content) > 200 else content)

def demo_mixed_scenario():
    """演示混合场景"""
    print("\n=== 场景4: 新增+下架+排名变化 ===")
    
    test_data = {
        'message': 'IMDB Top 250 综合变化',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '1部新电影进入榜单; 1部电影离开榜单; 2部电影排名发生变化',
            'new_entries': [
                {
                    'imdb_id': 'tt15398776',
                    'title': 'Oppenheimer',
                    'rank': 15,
                    'year': 2023,
                    'rating': 8.8
                }
            ],
            'removed_entries': [
                {
                    'imdb_id': 'tt0118799',
                    'title': 'Life Is Beautiful',
                    'old_rank': 249,
                    'year': 1997,
                    'rating': 8.6
                }
            ],
            'rank_changes': [
                {
                    'imdb_id': 'tt0111161',
                    'title': 'The Shawshank Redemption',
                    'old_rank': 2,
                    'new_rank': 1,
                    'change': '↑1'
                }
            ]
        }
    }
    
    notifier = Notifier()
    messages = notifier._format_wework_messages(test_data)
    
    print(f"📰 生成图文消息: {len(messages)} 条（因为有新增/下架电影）")
    
    for message in messages:
        if message['msgtype'] == 'news':
            articles = message['news']['articles']
            print(f"\n图文消息包含 {len(articles)} 个文章:")
            
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article['title']}")
                if '🆕' in article['title']:
                    print(f"     ✨ 新增电影信息")
                elif '📤' in article['title']:
                    print(f"     👋 下架电影信息")
                else:
                    print(f"     📋 主要信息")

def show_message_comparison():
    """显示消息类型对比"""
    print("\n=== 消息类型对比 ===")
    
    print("\n📰 图文消息 (news类型):")
    print("  ✅ 触发条件: 有新增或下架电影")
    print("  ✅ 显示效果: 卡片样式，包含图片")
    print("  ✅ 内容结构: 主文章 + 子文章")
    print("  ✅ 交互性: 可点击跳转")
    print("  ✅ 信息密度: 高，包含详细信息")
    
    print("\n📝 Markdown消息:")
    print("  ✅ 触发条件: 只有排名变化")
    print("  ✅ 显示效果: 文本格式")
    print("  ✅ 内容结构: 单一消息体")
    print("  ✅ 交互性: 无")
    print("  ✅ 信息密度: 中等，文本描述")

def demo_configuration():
    """演示配置选项"""
    print("\n=== 配置选项 ===")
    
    from config import Config
    
    print(f"图片功能启用: {Config.ENABLE_MOVIE_IMAGES}")
    print(f"Webhook类型: {Config.WEBHOOK_TYPE}")
    print(f"通知类型: {Config.NOTIFICATION_TYPE}")
    
    print("\n配置说明:")
    print("  ENABLE_MOVIE_IMAGES=true  # 启用图片功能")
    print("  WEBHOOK_TYPE=wework       # 企业微信类型")
    print("  NOTIFICATION_TYPE=webhook # 使用Webhook通知")

def main():
    """主演示函数"""
    demo_message_logic()
    demo_new_movies_scenario()
    demo_removed_movies_scenario()
    demo_rank_changes_scenario()
    demo_mixed_scenario()
    show_message_comparison()
    demo_configuration()
    
    print("\n=== 演示完成 ===")
    print("🎉 新增/下架电影图文消息功能已完成")
    print("📱 现在只有新增或下架电影时才会发送图文消息")
    print("🖼️ 图文消息包含电影海报和详细排名信息")
    print("📝 纯排名变化使用简洁的Markdown消息")

if __name__ == "__main__":
    main()
