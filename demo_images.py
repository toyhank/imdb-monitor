"""
电影图片功能演示
"""
import json
from config import setup_logging
from simple_movie_images import SimpleMovieImageFetcher
from notifier import Notifier

# 设置日志
logger = setup_logging()

def demo_simple_image_fetcher():
    """演示简化版图片获取器"""
    print("=== 演示简化版图片获取器 ===")
    
    fetcher = SimpleMovieImageFetcher()
    
    # 测试预定义的电影海报
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
        else:
            print(f"❌ 获取海报失败")
    
    return fetcher

def demo_wework_with_images():
    """演示企业微信图片消息"""
    print("\n=== 演示企业微信图片消息 ===")
    
    # 创建测试数据
    test_data = {
        'message': 'IMDB Top 250 变化检测 - 图片演示',
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
    
    # 格式化消息
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

def demo_send_test():
    """演示发送测试"""
    print("\n=== 演示发送测试 ===")
    
    from config import Config
    
    if not Config.WEBHOOK_URL or 'YOUR_KEY' in Config.WEBHOOK_URL:
        print("⚠️  请先配置真实的企业微信Webhook URL")
        return False
    
    # 创建测试数据
    test_data = {
        'message': 'IMDB Top 250 图片功能测试',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '图片功能演示消息',
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
        user_input = input("是否发送带图片的测试消息到企业微信群? (y/N): ").strip().lower()
        if user_input == 'y':
            print("发送测试消息...")
            
            notifier = Notifier()
            success = notifier.send_notification(test_data)
            
            if success:
                print("✅ 带图片的消息发送成功！")
                print("请检查企业微信群是否收到图片和文本消息")
            else:
                print("❌ 消息发送失败")
            
            return success
        else:
            print("跳过发送测试")
            return True
    except KeyboardInterrupt:
        print("\n跳过发送测试")
        return True

def show_image_config():
    """显示图片配置"""
    print("\n=== 图片功能配置 ===")
    
    from config import Config
    
    print(f"图片功能启用: {Config.ENABLE_MOVIE_IMAGES}")
    print(f"Webhook类型: {Config.WEBHOOK_TYPE}")
    print(f"通知类型: {Config.NOTIFICATION_TYPE}")
    
    if Config.ENABLE_MOVIE_IMAGES:
        print("✅ 图片功能已启用")
        print("   - 支持获取电影海报")
        print("   - 支持图片压缩和格式转换")
        print("   - 支持企业微信图片消息")
    else:
        print("❌ 图片功能已禁用")
        print("   要启用图片功能，请在config.env中设置:")
        print("   ENABLE_MOVIE_IMAGES=true")

def main():
    """主演示函数"""
    print("电影图片功能演示")
    print("=" * 50)
    
    try:
        # 显示配置
        show_image_config()
        
        # 演示图片获取
        fetcher = demo_simple_image_fetcher()
        
        # 演示消息格式化
        messages = demo_wework_with_images()
        
        # 演示发送测试
        demo_send_test()
        
        print("\n=== 演示完成 ===")
        print("图片功能已集成到IMDB监控系统中")
        print("当检测到电影排名变化时，会自动获取海报并发送到企业微信群")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
