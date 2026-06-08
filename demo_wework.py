"""
企业微信机器人消息格式演示
"""
import json
from notifier import Notifier

def demo_wework_messages():
    """演示不同场景的企业微信消息"""
    print("企业微信机器人消息格式演示")
    print("=" * 50)
    
    notifier = Notifier()
    
    # 场景1: 只有排名变化
    print("\n📊 场景1: 只有排名变化")
    print("-" * 30)
    
    data1 = {
        'message': 'IMDB Top 250 排名变化',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '5部电影排名发生变化',
            'rank_changes': [
                {'title': 'The Godfather', 'old_rank': 2, 'new_rank': 1, 'change': '↑1'},
                {'title': 'The Shawshank Redemption', 'old_rank': 1, 'new_rank': 2, 'change': '↓1'},
                {'title': 'The Dark Knight', 'old_rank': 4, 'new_rank': 3, 'change': '↑1'},
                {'title': '12 Angry Men', 'old_rank': 3, 'new_rank': 4, 'change': '↓1'},
                {'title': 'Schindler\'s List', 'old_rank': 6, 'new_rank': 5, 'change': '↑1'},
                {'title': 'The Lord of the Rings: The Return of the King', 'old_rank': 5, 'new_rank': 6, 'change': '↓1'},
            ]
        }
    }
    
    msg1 = notifier._format_wework_message(data1)
    print(msg1['markdown']['content'])
    
    # 场景2: 新增电影
    print("\n\n🆕 场景2: 新增电影")
    print("-" * 30)
    
    data2 = {
        'message': 'IMDB Top 250 新增电影',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '3部新电影进入榜单',
            'new_entries': [
                {'title': 'Oppenheimer', 'rank': 15, 'year': 2023, 'rating': 8.8},
                {'title': 'Everything Everywhere All at Once', 'rank': 45, 'year': 2022, 'rating': 8.1},
                {'title': 'Top Gun: Maverick', 'rank': 78, 'year': 2022, 'rating': 8.3},
                {'title': 'Dune', 'rank': 156, 'year': 2021, 'rating': 8.0},
            ]
        }
    }
    
    msg2 = notifier._format_wework_message(data2)
    print(msg2['markdown']['content'])
    
    # 场景3: 电影离开榜单
    print("\n\n📤 场景3: 电影离开榜单")
    print("-" * 30)
    
    data3 = {
        'message': 'IMDB Top 250 电影离开',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '2部电影离开榜单',
            'removed_entries': [
                {'title': 'The Green Mile', 'old_rank': 248, 'year': 1999, 'rating': 8.6},
                {'title': 'Life Is Beautiful', 'old_rank': 250, 'year': 1997, 'rating': 8.6},
            ]
        }
    }
    
    msg3 = notifier._format_wework_message(data3)
    print(msg3['markdown']['content'])
    
    # 场景4: 综合变化（最常见）
    print("\n\n🎬 场景4: 综合变化")
    print("-" * 30)
    
    data4 = {
        'message': 'IMDB Top 250 综合变化',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': '3部电影排名发生变化; 2部新电影进入榜单; 1部电影离开榜单',
            'rank_changes': [
                {'title': 'The Godfather', 'old_rank': 2, 'new_rank': 1, 'change': '↑1'},
                {'title': 'The Shawshank Redemption', 'old_rank': 1, 'new_rank': 2, 'change': '↓1'},
                {'title': 'Pulp Fiction', 'old_rank': 8, 'new_rank': 7, 'change': '↑1'},
            ],
            'new_entries': [
                {'title': 'Oppenheimer', 'rank': 15, 'year': 2023, 'rating': 8.8},
                {'title': 'Barbie', 'rank': 89, 'year': 2023, 'rating': 7.9},
            ],
            'removed_entries': [
                {'title': 'The Green Mile', 'old_rank': 248, 'year': 1999, 'rating': 8.6},
            ]
        }
    }
    
    msg4 = notifier._format_wework_message(data4)
    print(msg4['markdown']['content'])
    
    # 场景5: 大量变化（显示截断效果）
    print("\n\n📈 场景5: 大量变化（显示截断效果）")
    print("-" * 30)
    
    # 生成大量排名变化
    rank_changes = []
    for i in range(15):
        rank_changes.append({
            'title': f'Movie {i+1}',
            'old_rank': i+10,
            'new_rank': i+5,
            'change': '↑5'
        })
    
    data5 = {
        'message': 'IMDB Top 250 大量变化',
        'details': {
            'timestamp': '2023-12-01T09:00:00',
            'summary': f'{len(rank_changes)}部电影排名发生变化',
            'rank_changes': rank_changes
        }
    }
    
    msg5 = notifier._format_wework_message(data5)
    print(msg5['markdown']['content'])

def show_json_format():
    """显示JSON格式"""
    print("\n\n📋 企业微信机器人API格式")
    print("=" * 50)
    
    example_json = {
        "msgtype": "markdown",
        "markdown": {
            "content": "# 🎬 IMDB Top 250 变化通知\n\n**时间**: 2023-12-01 09:00:00\n**摘要**: 示例消息\n\n## 📊 排名变化\n- 🔺 **电影名称**: #旧排名 → #新排名 (变化)\n\n---\n*IMDB Top 250 监控系统*"
        }
    }
    
    print("标准JSON格式:")
    print(json.dumps(example_json, indent=2, ensure_ascii=False))
    
    print("\n支持的消息类型:")
    print("1. markdown - Markdown格式消息（当前使用）")
    print("2. text - 纯文本消息")
    print("3. image - 图片消息")
    print("4. news - 图文消息")

def show_setup_guide():
    """显示设置指南"""
    print("\n\n⚙️ 企业微信机器人设置指南")
    print("=" * 50)
    
    print("1. 在企业微信群中添加机器人:")
    print("   - 进入群聊 → 点击右上角'...' → 群机器人 → 添加机器人")
    print("   - 设置机器人名称（如：IMDB监控）")
    print("   - 复制生成的Webhook URL")
    
    print("\n2. 配置程序:")
    print("   编辑 config.env 文件:")
    print("   WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY")
    print("   NOTIFICATION_TYPE=webhook")
    print("   WEBHOOK_TYPE=wework")
    
    print("\n3. 测试配置:")
    print("   python test_wework.py")
    
    print("\n4. 运行监控:")
    print("   python main.py --once  # 执行一次")
    print("   python main.py         # 持续运行")
    
    print("\n📖 详细文档: WEWORK_SETUP.md")

def main():
    """主函数"""
    demo_wework_messages()
    show_json_format()
    show_setup_guide()

if __name__ == "__main__":
    main()
