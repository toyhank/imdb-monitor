"""
电影图片功能测试脚本
"""
import json
import logging
from config import setup_logging
from movie_images import MovieImageFetcher
from notifier import Notifier

# 设置日志
logger = setup_logging()

def test_image_fetcher():
    """测试图片获取器"""
    print("=== 测试电影图片获取器 ===")
    
    fetcher = MovieImageFetcher()
    
    # 测试单个电影海报获取
    test_movies = [
        {'imdb_id': 'tt0111161', 'title': 'The Shawshank Redemption'},
        {'imdb_id': 'tt0068646', 'title': 'The Godfather'},
        {'imdb_id': 'tt0468569', 'title': 'The Dark Knight'},
    ]
    
    print(f"测试获取 {len(test_movies)} 部电影的海报...")
    
    for movie in test_movies:
        print(f"\n获取《{movie['title']}》海报...")
        poster = fetcher.get_movie_poster(movie['imdb_id'], movie['title'])
        
        if poster:
            print(f"✅ 成功获取海报")
            print(f"   图片大小: {poster['size']} bytes")
            print(f"   MD5: {poster['md5'][:16]}...")
            print(f"   Base64长度: {len(poster['base64'])} 字符")
            print(f"   原始URL: {poster['url'][:50]}...")
        else:
            print(f"❌ 获取海报失败")
    
    # 测试批量获取
    print(f"\n测试批量获取...")
    posters = fetcher.get_multiple_posters(test_movies, max_count=2)
    print(f"批量获取结果: {len(posters)} 个海报")
    
    return posters

def test_wework_image_message():
    """测试企业微信图片消息格式"""
    print("\n=== 测试企业微信图片消息格式 ===")
    
    # 创建测试数据
    test_data = {
        'message': 'IMDB Top 250 变化检测 - 图片测试',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '2部电影排名发生变化',
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
        
        if message['msgtype'] == 'image':
            image_info = message['image']
            print(f"  图片MD5: {image_info['md5']}")
            print(f"  Base64长度: {len(image_info['base64'])} 字符")
        elif message['msgtype'] == 'markdown':
            content = message['markdown']['content']
            print(f"  内容长度: {len(content)} 字符")
            print(f"  内容预览: {content[:100]}...")
    
    return messages

def test_send_with_images():
    """测试发送带图片的消息"""
    print("\n=== 测试发送带图片的消息 ===")
    
    from config import Config
    
    if not Config.WEBHOOK_URL or 'YOUR_KEY' in Config.WEBHOOK_URL:
        print("⚠️  请先配置真实的企业微信Webhook URL")
        return False
    
    # 创建测试数据
    test_data = {
        'message': 'IMDB Top 250 图片测试',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '图片功能测试消息',
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
    
    print("发送测试消息（包含图片）...")
    
    notifier = Notifier()
    success = notifier.send_notification(test_data)
    
    if success:
        print("✅ 带图片的消息发送成功！")
        print("请检查企业微信群是否收到图片和文本消息")
    else:
        print("❌ 消息发送失败")
    
    return success

def test_image_config():
    """测试图片功能配置"""
    print("\n=== 测试图片功能配置 ===")
    
    from config import Config
    
    print(f"图片功能启用状态: {Config.ENABLE_MOVIE_IMAGES}")
    print(f"Webhook类型: {Config.WEBHOOK_TYPE}")
    print(f"通知类型: {Config.NOTIFICATION_TYPE}")
    
    # 测试图片获取器加载
    notifier = Notifier()
    image_fetcher = notifier._get_image_fetcher()
    
    if image_fetcher:
        print("✅ 图片获取器加载成功")
    else:
        print("❌ 图片获取器加载失败")
    
    return image_fetcher is not None

def demo_image_workflow():
    """演示完整的图片工作流程"""
    print("\n=== 演示完整图片工作流程 ===")
    
    # 1. 模拟检测到变化
    print("1. 模拟检测到电影排名变化...")
    changes = [
        {'imdb_id': 'tt0111161', 'title': 'The Shawshank Redemption', 'old_rank': 2, 'new_rank': 1, 'change': '↑1'},
        {'imdb_id': 'tt0068646', 'title': 'The Godfather', 'old_rank': 1, 'new_rank': 2, 'change': '↓1'},
    ]
    
    # 2. 获取电影海报
    print("2. 获取电影海报...")
    fetcher = MovieImageFetcher()
    posters = fetcher.get_multiple_posters(changes, max_count=2)
    print(f"   获取到 {len(posters)} 个海报")
    
    # 3. 格式化消息
    print("3. 格式化企业微信消息...")
    notification_data = {
        'message': '演示消息',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '演示图片功能',
            'rank_changes': changes
        }
    }
    
    notifier = Notifier()
    messages = notifier._format_wework_messages(notification_data)
    print(f"   生成 {len(messages)} 条消息")
    
    # 4. 显示消息结构
    print("4. 消息结构:")
    for i, msg in enumerate(messages, 1):
        if msg['msgtype'] == 'image':
            print(f"   消息{i}: 图片消息")
        else:
            print(f"   消息{i}: 文本消息")
    
    return messages

def main():
    """主测试函数"""
    print("电影图片功能测试")
    print("=" * 50)
    
    try:
        # 测试配置
        config_ok = test_image_config()
        
        if not config_ok:
            print("图片功能配置有问题，跳过后续测试")
            return
        
        # 测试图片获取
        posters = test_image_fetcher()
        
        # 测试消息格式化
        messages = test_wework_image_message()
        
        # 演示完整流程
        demo_messages = demo_image_workflow()
        
        # 询问是否发送测试消息
        from config import Config
        if Config.WEBHOOK_URL and 'YOUR_KEY' not in Config.WEBHOOK_URL:
            try:
                user_input = input("\n是否发送带图片的测试消息到企业微信群? (y/N): ").strip().lower()
                if user_input == 'y':
                    test_send_with_images()
                else:
                    print("跳过发送测试")
            except KeyboardInterrupt:
                print("\n跳过发送测试")
        else:
            print("\n💡 要测试实际发送，请配置真实的企业微信Webhook URL")
        
        print("\n=== 测试完成 ===")
        print("图片功能已集成到通知系统中")
        print("运行 'python main.py --once' 查看实际效果")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
