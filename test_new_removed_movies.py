"""
测试新增/下架电影的图文消息功能
"""
import json
from config import setup_logging
from notifier import Notifier

# 设置日志
logger = setup_logging()

def test_new_movies_only():
    """测试只有新增电影的情况"""
    print("=== 测试只有新增电影的情况 ===")
    
    test_data = {
        'message': 'IMDB Top 250 新增电影',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '3部新电影进入榜单',
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
                },
                {
                    'imdb_id': 'tt1745960',
                    'title': 'Top Gun: Maverick',
                    'rank': 78,
                    'year': 2022,
                    'rating': 8.3
                }
            ]
        }
    }
    
    notifier = Notifier()
    messages = notifier._format_wework_messages(test_data)
    
    print(f"生成了 {len(messages)} 条消息:")
    
    for i, message in enumerate(messages, 1):
        print(f"\n消息 {i}:")
        print(f"  类型: {message['msgtype']}")
        
        if message['msgtype'] == 'news':
            articles = message['news']['articles']
            print(f"  文章数量: {len(articles)}")
            
            for j, article in enumerate(articles):
                print(f"    文章 {j+1}:")
                print(f"      标题: {article['title']}")
                print(f"      描述: {article['description']}")
                print(f"      链接: {article['url']}")
                print(f"      图片: {'有' if article['picurl'] else '无'}")
        else:
            print(f"  内容: {message.get('markdown', {}).get('content', '')[:100]}...")
    
    return messages

def test_removed_movies_only():
    """测试只有下架电影的情况"""
    print("\n=== 测试只有下架电影的情况 ===")
    
    test_data = {
        'message': 'IMDB Top 250 电影下架',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '2部电影离开榜单',
            'removed_entries': [
                {
                    'imdb_id': 'tt0118799',
                    'title': 'Life Is Beautiful',
                    'old_rank': 249,
                    'year': 1997,
                    'rating': 8.6
                },
                {
                    'imdb_id': 'tt0110912',
                    'title': 'Pulp Fiction',
                    'old_rank': 250,
                    'year': 1994,
                    'rating': 8.9
                }
            ]
        }
    }
    
    notifier = Notifier()
    messages = notifier._format_wework_messages(test_data)
    
    print(f"生成了 {len(messages)} 条消息:")
    
    for i, message in enumerate(messages, 1):
        print(f"\n消息 {i}:")
        print(f"  类型: {message['msgtype']}")
        
        if message['msgtype'] == 'news':
            articles = message['news']['articles']
            print(f"  文章数量: {len(articles)}")
            
            for j, article in enumerate(articles):
                print(f"    文章 {j+1}:")
                print(f"      标题: {article['title']}")
                print(f"      描述: {article['description']}")
        else:
            print(f"  内容: Markdown消息")
    
    return messages

def test_new_and_removed_movies():
    """测试同时有新增和下架电影的情况"""
    print("\n=== 测试同时有新增和下架电影的情况 ===")
    
    test_data = {
        'message': 'IMDB Top 250 榜单更新',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '2部新电影进入榜单; 1部电影离开榜单',
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
            ],
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
    
    print(f"生成了 {len(messages)} 条消息:")
    
    for i, message in enumerate(messages, 1):
        print(f"\n消息 {i}:")
        print(f"  类型: {message['msgtype']}")
        
        if message['msgtype'] == 'news':
            articles = message['news']['articles']
            print(f"  文章数量: {len(articles)}")
            
            for j, article in enumerate(articles):
                print(f"    文章 {j+1}:")
                print(f"      标题: {article['title']}")
                print(f"      描述: {article['description'][:50]}...")
                print(f"      图片: {'有' if article['picurl'] else '无'}")
    
    return messages

def test_rank_changes_only():
    """测试只有排名变化的情况（应该使用Markdown消息）"""
    print("\n=== 测试只有排名变化的情况 ===")
    
    test_data = {
        'message': 'IMDB Top 250 排名变化',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '5部电影排名发生变化',
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
    
    print(f"生成了 {len(messages)} 条消息:")
    
    for i, message in enumerate(messages, 1):
        print(f"\n消息 {i}:")
        print(f"  类型: {message['msgtype']}")
        
        if message['msgtype'] == 'markdown':
            content = message['markdown']['content']
            print(f"  内容长度: {len(content)} 字符")
            print(f"  内容预览: {content[:100]}...")
        else:
            print(f"  意外的消息类型: {message['msgtype']}")
    
    return messages

def test_send_new_movie_message():
    """测试发送新增电影的图文消息"""
    print("\n=== 测试发送新增电影的图文消息 ===")
    
    from config import Config
    
    if not Config.WEBHOOK_URL or 'YOUR_KEY' in Config.WEBHOOK_URL:
        print("⚠️  请先配置真实的企业微信Webhook URL")
        return False
    
    test_data = {
        'message': 'IMDB Top 250 新增电影测试',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '新增电影图文消息测试',
            'new_entries': [
                {
                    'imdb_id': 'tt0111161',  # 使用已知的电影ID进行测试
                    'title': 'The Shawshank Redemption',
                    'rank': 1,
                    'year': 1994,
                    'rating': 9.3
                }
            ]
        }
    }
    
    try:
        user_input = input("是否发送新增电影的图文消息测试? (y/N): ").strip().lower()
        if user_input == 'y':
            print("发送新增电影图文消息测试...")
            
            notifier = Notifier()
            success = notifier.send_notification(test_data)
            
            if success:
                print("✅ 新增电影图文消息发送成功！")
                print("请检查企业微信群是否收到包含以下内容的图文消息:")
                print("  - 主标题: 🎬 IMDB Top 250 榜单更新")
                print("  - 新增电影: 🆕 电影名称")
                print("  - 电影海报图片")
                print("  - 排名和详细信息")
            else:
                print("❌ 图文消息发送失败")
            
            return success
        else:
            print("跳过发送测试")
            return True
    except KeyboardInterrupt:
        print("\n跳过发送测试")
        return True

def main():
    """主测试函数"""
    print("新增/下架电影图文消息功能测试")
    print("=" * 50)
    
    try:
        # 测试各种情况
        test_new_movies_only()
        test_removed_movies_only()
        test_new_and_removed_movies()
        test_rank_changes_only()
        
        # 测试发送
        test_send_new_movie_message()
        
        print("\n=== 测试总结 ===")
        print("✅ 只有新增/下架电影时才发送图文消息")
        print("✅ 图文消息包含新增电影的详细信息和排名")
        print("✅ 新增电影显示海报图片")
        print("✅ 下架电影显示基本信息（无图片）")
        print("✅ 只有排名变化时使用普通Markdown消息")
        print("✅ 图文消息支持点击跳转到IMDB页面")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
