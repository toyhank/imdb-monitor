"""
测试企业微信图文消息功能
"""
import json
from config import setup_logging
from notifier import Notifier

# 设置日志
logger = setup_logging()

def test_news_message_format():
    """测试图文消息格式"""
    print("=== 测试企业微信图文消息格式 ===")
    
    # 创建测试数据
    test_data = {
        'message': 'IMDB Top 250 变化检测 - 图文消息测试',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '3部电影排名发生变化，包含海报图片',
            'rank_changes': [
                {
                    'imdb_id': 'tt0111161',
                    'title': 'The Shawshank Redemption',
                    'old_rank': 2,
                    'new_rank': 1,
                    'change': '↑1',
                    'year': 1994,
                    'rating': 9.3
                },
                {
                    'imdb_id': 'tt0068646',
                    'title': 'The Godfather',
                    'old_rank': 1,
                    'new_rank': 2,
                    'change': '↓1',
                    'year': 1972,
                    'rating': 9.2
                },
                {
                    'imdb_id': 'tt0468569',
                    'title': 'The Dark Knight',
                    'old_rank': 4,
                    'new_rank': 3,
                    'change': '↑1',
                    'year': 2008,
                    'rating': 9.0
                }
            ]
        }
    }
    
    # 测试消息格式化
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
                print(f"      链接: {article['url']}")
                print(f"      图片: {article['picurl'][:50]}..." if article['picurl'] else "      图片: 无")
                
        elif message['msgtype'] == 'markdown':
            content = message['markdown']['content']
            print(f"  内容长度: {len(content)} 字符")
            print(f"  内容预览: {content[:100]}...")
    
    return messages

def test_news_message_json():
    """测试图文消息JSON格式"""
    print("\n=== 测试图文消息JSON格式 ===")
    
    # 模拟有图片的情况
    mock_movie_images = {
        'tt0111161': {
            'base64': 'mock_base64_data',
            'md5': 'mock_md5_hash',
            'size': 12345,
            'url': 'https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_SX300.jpg',
            'title': 'The Shawshank Redemption'
        },
        'tt0068646': {
            'base64': 'mock_base64_data_2',
            'md5': 'mock_md5_hash_2',
            'size': 23456,
            'url': 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzAwMjU2MzY@._V1_SX300.jpg',
            'title': 'The Godfather'
        }
    }
    
    test_data = {
        'message': 'IMDB Top 250 变化检测',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '2部电影排名发生变化',
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
    news_message = notifier._create_news_message(test_data, mock_movie_images)
    
    print("图文消息JSON格式:")
    print(json.dumps(news_message, indent=2, ensure_ascii=False))
    
    return news_message

def test_fallback_to_markdown():
    """测试回退到Markdown消息"""
    print("\n=== 测试回退到Markdown消息 ===")
    
    # 创建没有图片的测试数据
    test_data = {
        'message': 'IMDB Top 250 变化检测 - 无图片',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '1部电影排名发生变化（无图片）',
            'rank_changes': [
                {
                    'imdb_id': 'tt0050083',
                    'title': '12 Angry Men',
                    'old_rank': 5,
                    'new_rank': 4,
                    'change': '↑1'
                }
            ]
        }
    }
    
    # 模拟图片功能禁用的情况
    notifier = Notifier()
    
    # 临时禁用图片功能
    original_enable = notifier.config.ENABLE_MOVIE_IMAGES
    notifier.config.ENABLE_MOVIE_IMAGES = False
    
    try:
        messages = notifier._format_wework_messages(test_data)
        
        print(f"生成了 {len(messages)} 条消息:")
        for i, message in enumerate(messages, 1):
            print(f"  消息 {i}: {message['msgtype']}")
            if message['msgtype'] == 'markdown':
                print(f"    内容长度: {len(message['markdown']['content'])} 字符")
    
    finally:
        # 恢复原始设置
        notifier.config.ENABLE_MOVIE_IMAGES = original_enable
    
    return messages

def test_send_news_message():
    """测试发送图文消息"""
    print("\n=== 测试发送图文消息 ===")
    
    from config import Config
    
    if not Config.WEBHOOK_URL or 'YOUR_KEY' in Config.WEBHOOK_URL:
        print("⚠️  请先配置真实的企业微信Webhook URL")
        return False
    
    # 创建测试数据
    test_data = {
        'message': 'IMDB Top 250 图文消息测试',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '图文消息功能测试',
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
    
    try:
        user_input = input("是否发送图文消息测试到企业微信群? (y/N): ").strip().lower()
        if user_input == 'y':
            print("发送图文消息测试...")
            
            notifier = Notifier()
            success = notifier.send_notification(test_data)
            
            if success:
                print("✅ 图文消息发送成功！")
                print("请检查企业微信群是否收到图文消息")
                print("图文消息应该包含:")
                print("  - 主标题和摘要")
                print("  - 电影海报图片")
                print("  - 可点击的链接")
            else:
                print("❌ 图文消息发送失败")
            
            return success
        else:
            print("跳过发送测试")
            return True
    except KeyboardInterrupt:
        print("\n跳过发送测试")
        return True

def show_news_message_features():
    """显示图文消息功能特性"""
    print("\n=== 图文消息功能特性 ===")
    print("✅ 图片和文字合并在一条消息中")
    print("✅ 支持多个文章（主文章 + 电影详情）")
    print("✅ 每个文章都有标题、描述、图片和链接")
    print("✅ 点击可跳转到IMDB电影页面")
    print("✅ 在企业微信中显示为卡片样式")
    print("✅ 自动回退到Markdown格式（无图片时）")
    
    print("\n图文消息结构:")
    print("  主文章: IMDB Top 250 变化通知")
    print("    ├─ 标题: 🎬 IMDB Top 250 变化通知")
    print("    ├─ 描述: 时间和摘要信息")
    print("    ├─ 图片: 第一部电影的海报")
    print("    └─ 链接: IMDB Top 250 页面")
    print("  子文章: 每部电影的详细信息")
    print("    ├─ 标题: 📈/📉 电影名称")
    print("    ├─ 描述: 排名变化详情")
    print("    ├─ 图片: 电影海报")
    print("    └─ 链接: 电影详情页面")

def main():
    """主测试函数"""
    print("企业微信图文消息功能测试")
    print("=" * 50)
    
    try:
        # 显示功能特性
        show_news_message_features()
        
        # 测试消息格式
        messages = test_news_message_format()
        
        # 测试JSON格式
        news_message = test_news_message_json()
        
        # 测试回退机制
        fallback_messages = test_fallback_to_markdown()
        
        # 测试发送
        test_send_news_message()
        
        print("\n=== 测试完成 ===")
        print("图文消息功能已集成到通知系统中")
        print("现在电影图片和文字会合并在一条卡片消息中显示")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
