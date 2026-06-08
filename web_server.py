"""
IMDB Top 250 监控系统 Web 服务器
提供前端界面和API接口
"""
import os
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# 导入现有模块
from config import Config, setup_logging
from database import DatabaseManager
from hybrid_scraper import HybridScraper as IMDBScraper
from change_detector import ChangeDetector
from notifier import Notifier
from google_analytics import google_analytics

# 设置日志
logger = setup_logging()

# 创建Flask应用
app = Flask(__name__, 
           static_folder='web/static',
           template_folder='web')
CORS(app)

# 全局变量
db = DatabaseManager()
scraper = IMDBScraper()
detector = ChangeDetector()
notifier = Notifier()

# 用户配置存储
user_configs = {}

class WebConfig:
    """Web界面配置管理"""
    
    def __init__(self):
        self.config_file = 'web_config.json'
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
        except Exception as e:
            logger.error(f"加载Web配置失败: {e}")
            self.config = {}
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存Web配置失败: {e}")
    
    def update_config(self, config_data):
        """更新配置"""
        self.config.update(config_data)
        self.save_config()
        
        # 更新全局配置
        if 'webhook_key' in config_data:
            webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={config_data['webhook_key']}"
            Config.WEBHOOK_URL = webhook_url
            
        if 'enable_images' in config_data:
            Config.ENABLE_MOVIE_IMAGES = config_data['enable_images']

web_config = WebConfig()

@app.route('/')
def index():
    """主页"""
    # 读取HTML文件并注入配置和统计代码
    try:
        with open('web/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 注入Google Analytics统计代码
        if google_analytics.is_enabled():
            analytics_script = google_analytics.get_tracking_script()
            # 在</head>标签前插入统计代码
            html_content = html_content.replace('</head>', f'{analytics_script}\n</head>')
            logger.info("Google Analytics统计代码已注入到页面")

        # 根据配置决定是否显示统计卡片
        if not Config.SHOW_ANALYTICS_UI:
            # 隐藏统计卡片
            html_content = html_content.replace(
                'class="card analytics-card"',
                'class="card analytics-card" style="display: none;"'
            )
            # 禁用统计状态加载（但保留统计脚本）
            html_content = html_content.replace(
                'this.loadAnalyticsStatus();',
                '// this.loadAnalyticsStatus(); // 已禁用界面显示'
            )
            logger.info("统计界面已隐藏")

        return html_content
    except Exception as e:
        logger.error(f"加载主页失败: {e}")
        return send_from_directory('web', 'index.html')

@app.route('/api/status')
def api_status():
    """获取系统状态"""
    try:
        latest_data = db.get_latest_data()
        
        # 计算下次检查时间（假设每天9点）
        now = datetime.now()
        next_check = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now.hour >= 9:
            next_check += timedelta(days=1)
        
        status = {
            'status': 'running',  # 简化状态，实际可以检查进程
            'movie_count': len(latest_data) if latest_data else 0,
            'last_update': datetime.now().isoformat(),
            'next_check': next_check.isoformat(),
            'webhook_configured': bool(Config.WEBHOOK_URL and 'YOUR_KEY' not in Config.WEBHOOK_URL)
        }
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies')
def api_movies():
    """获取电影数据"""
    try:
        movies = db.get_latest_data()
        return jsonify(movies or [])
    except Exception as e:
        logger.error(f"获取电影数据失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/changes')
def api_changes():
    """获取最近变化"""
    try:
        # 从数据库获取最近的变化记录
        import sqlite3
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT change_date, change_type, title, chinese_title, year, rating, old_rank, new_rank
            FROM changes
            ORDER BY change_date DESC
            LIMIT 10
        """)

        changes = []
        for row in cursor.fetchall():
            change_date, change_type, movie_title, chinese_title, year, rating, old_rank, new_rank = row

            # 优先使用中文标题
            display_title = chinese_title or movie_title

            if change_type == 'new':
                year_info = f" ({year})" if year else ""
                rating_info = f" 评分:{rating}" if rating else ""
                description = f"🆕 {display_title}{year_info} 新进榜单 (#{new_rank}){rating_info}"
            elif change_type == 'removed':
                year_info = f" ({year})" if year else ""
                description = f"📤 {display_title}{year_info} 离开榜单 (原#{old_rank})"
            else:
                year_info = f" ({year})" if year else ""
                description = f"📊 {display_title}{year_info} 排名变化: #{old_rank} → #{new_rank}"

            changes.append({
                'timestamp': change_date,
                'type': change_type,
                'description': description
            })
        
        conn.close()
        return jsonify(changes)
    except Exception as e:
        logger.error(f"获取变化记录失败: {e}")
        return jsonify([])

@app.route('/api/config', methods=['POST'])
def api_save_config():
    """保存用户配置"""
    try:
        config_data = request.get_json()
        
        # 验证webhook key
        if not config_data.get('webhook_key'):
            return jsonify({'error': '请输入企业微信机器人Key'}), 400
        
        # 更新配置
        web_config.update_config(config_data)
        
        return jsonify({'message': '配置保存成功'})
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-notification', methods=['POST'])
def api_test_notification():
    """发送测试通知"""
    try:
        data = request.get_json()
        webhook_key = data.get('webhook_key')
        
        if not webhook_key:
            return jsonify({'error': '请提供企业微信机器人Key'}), 400
        
        # 临时设置webhook URL
        original_url = Config.WEBHOOK_URL
        Config.WEBHOOK_URL = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_key}"
        
        try:
            # 创建测试通知数据
            test_data = {
                'message': 'IMDB Top 250 监控系统测试通知',
                'details': {
                    'timestamp': datetime.now().isoformat(),
                    'summary': '这是一条测试消息，用于验证企业微信机器人配置是否正确',
                    'test': True
                }
            }
            
            # 发送通知
            success = notifier.send_notification(test_data)
            
            if success:
                return jsonify({'message': '测试通知发送成功'})
            else:
                return jsonify({'error': '测试通知发送失败'}), 500
                
        finally:
            # 恢复原始URL
            Config.WEBHOOK_URL = original_url
            
    except Exception as e:
        logger.error(f"发送测试通知失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check', methods=['POST'])
def api_manual_check():
    """手动执行检查"""
    logger.info("收到手动检查请求")
    print("DEBUG: 收到手动检查请求")
    try:
        # 在后台线程中执行检查
        def run_check():
            try:
                logger.info("开始手动检查...")
                
                # 爬取数据
                current_data = scraper.scrape_top_250()
                if not current_data:
                    logger.error("爬取数据失败")
                    return
                
                # 获取历史数据
                previous_data = db.get_latest_data()
                
                # 检测变化
                if previous_data:
                    changes = detector.detect_changes(previous_data, current_data)
                    
                    if changes['has_changes']:
                        # 发送通知
                        notification_data = detector.format_changes_for_notification(changes)
                        notifier.send_notification(notification_data)
                        
                        # 保存变化记录
                        db.save_changes(changes)
                        logger.info(f"检测到变化并发送通知: {changes['summary']}")
                    else:
                        logger.info("未检测到变化")
                
                # 保存当前数据
                db.save_data(current_data)
                logger.info("手动检查完成")
                
            except Exception as e:
                logger.error(f"手动检查失败: {e}")
        
        # 启动后台线程
        thread = threading.Thread(target=run_check)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': '检查已开始，请稍后查看结果'})
        
    except Exception as e:
        logger.error(f"启动手动检查失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def api_history():
    """获取完整历史记录"""
    try:
        import sqlite3
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT change_date, change_type, title, chinese_title, year, rating, old_rank, new_rank
            FROM changes
            ORDER BY change_date DESC
            LIMIT 50
        """)

        history = []
        for row in cursor.fetchall():
            change_date, change_type, movie_title, chinese_title, year, rating, old_rank, new_rank = row

            # 优先使用中文标题
            display_title = chinese_title or movie_title

            if change_type == 'new':
                year_info = f" ({year})" if year else ""
                rating_info = f" 评分:{rating}" if rating else ""
                description = f"🆕 {display_title}{year_info} 新进榜单 (#{new_rank}){rating_info}"
            elif change_type == 'removed':
                year_info = f" ({year})" if year else ""
                description = f"📤 {display_title}{year_info} 离开榜单 (原#{old_rank})"
            else:
                year_info = f" ({year})" if year else ""
                description = f"📊 {display_title}{year_info} 排名变化: #{old_rank} → #{new_rank}"

            history.append({
                'timestamp': change_date,
                'type': change_type,
                'description': description
            })
        
        conn.close()
        return jsonify(history)
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        return jsonify([])

@app.route('/api/download-excel')
def api_download_excel():
    """下载Excel数据"""
    try:
        # 获取所有数据
        movies = db.get_latest_data()

        if not movies:
            return jsonify({'error': '没有数据可导出'}), 400

        # 创建Excel文件
        import tempfile
        import pandas as pd

        # 准备导出数据
        export_data = []
        for movie in movies:
            # 处理列表字段
            directors_str = ', '.join(movie.get('directors', [])) if movie.get('directors') else ''
            countries_str = ', '.join(movie.get('countries', [])) if movie.get('countries') else ''
            genres_str = ', '.join(movie.get('genres', [])) if movie.get('genres') else ''
            cast_str = ', '.join([f"{actor.get('name', '')}" for actor in movie.get('cast', [])]) if movie.get('cast') else ''

            export_data.append({
                '排名': movie.get('rank'),
                '中文标题': movie.get('chinese_title', ''),
                '原标题': movie.get('title', ''),
                '年份': movie.get('year'),
                'IMDB评分': movie.get('rating'),
                'TMDB评分': movie.get('tmdb_rating'),
                '导演': directors_str,
                '国家': countries_str,
                '类型': genres_str,
                '时长(分钟)': movie.get('runtime'),
                '简介': movie.get('overview', ''),
                '演员': cast_str,
                '投票数': movie.get('vote_count'),
                '热度': movie.get('popularity'),
                '发布日期': movie.get('release_date', ''),
                '原始语言': movie.get('original_language', ''),
                '预算': movie.get('budget'),
                '票房': movie.get('revenue'),
                'IMDB_ID': movie.get('imdb_id', ''),
                'TMDB_ID': movie.get('tmdb_id', ''),
                '海报路径': movie.get('poster_path', '')
            })

        # 创建DataFrame
        df = pd.DataFrame(export_data)

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name

        # 写入Excel文件
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='IMDB Top 250', index=False)

            # 获取工作表并调整列宽
            worksheet = writer.sheets['IMDB Top 250']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # 最大宽度50
                worksheet.column_dimensions[column_letter].width = adjusted_width

        # 发送文件
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f'IMDB_Top250_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.error(f"导出Excel失败: {e}")
        return jsonify({'error': f'导出失败: {str(e)}'}), 500

@app.route('/api/export')
def api_export():
    """导出Excel数据"""
    try:
        # 获取所有数据
        movies = db.get_latest_data()

        if not movies:
            return jsonify({'error': '没有数据可导出'}), 400

        # 创建Excel文件
        import tempfile
        import pandas as pd

        # 准备导出数据
        export_data = []
        for movie in movies:
            # 处理列表字段
            directors_str = ', '.join(movie.get('directors', [])) if movie.get('directors') else ''
            countries_str = ', '.join(movie.get('countries', [])) if movie.get('countries') else ''
            genres_str = ', '.join(movie.get('genres', [])) if movie.get('genres') else ''
            cast_str = ', '.join([f"{actor.get('name', '')}" for actor in movie.get('cast', [])]) if movie.get('cast') else ''

            export_data.append({
                '排名': movie.get('rank'),
                '中文标题': movie.get('chinese_title', ''),
                '原标题': movie.get('title', ''),
                '年份': movie.get('year'),
                'IMDB评分': movie.get('rating'),
                'TMDB评分': movie.get('tmdb_rating'),
                '导演': directors_str,
                '国家': countries_str,
                '类型': genres_str,
                '时长(分钟)': movie.get('runtime'),
                '简介': movie.get('overview', ''),
                '演员': cast_str,
                '投票数': movie.get('vote_count'),
                '热度': movie.get('popularity'),
                '发布日期': movie.get('release_date', ''),
                '原始语言': movie.get('original_language', ''),
                '预算': movie.get('budget'),
                '票房': movie.get('revenue'),
                'IMDB_ID': movie.get('imdb_id', ''),
                'TMDB_ID': movie.get('tmdb_id', ''),
                '海报路径': movie.get('poster_path', '')
            })

        # 创建DataFrame
        df = pd.DataFrame(export_data)

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name

        # 写入Excel文件
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='IMDB Top 250', index=False)

            # 获取工作表并调整列宽
            worksheet = writer.sheets['IMDB Top 250']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # 最大宽度50
                worksheet.column_dimensions[column_letter].width = adjusted_width

        # 发送文件
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f'IMDB_Top250_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.error(f"导出Excel失败: {e}")
        return jsonify({'error': f'导出失败: {str(e)}'}), 500

# Google Analytics API - 可选择性启用
if Config.ENABLE_ANALYTICS:
    @app.route('/api/analytics/scripts')
    def get_analytics_scripts():
        """获取Google Analytics脚本"""
        try:
            scripts = google_analytics.get_tracking_script()
            return jsonify({
                'scripts': scripts,
                'enabled': google_analytics.is_enabled(),
                'status': google_analytics.get_config_status()
            })
        except Exception as e:
            logger.error(f"获取统计脚本失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/analytics/status')
    def get_analytics_status():
        """获取Google Analytics状态"""
        try:
            return jsonify(google_analytics.get_config_status())
        except Exception as e:
            logger.error(f"获取统计状态失败: {e}")
            return jsonify({'error': str(e)}), 500
else:
    # 如果统计功能被禁用，返回空响应
    @app.route('/api/analytics/scripts')
    def get_analytics_scripts():
        return jsonify({'scripts': '', 'enabled': False, 'status': {'enabled': False}})

    @app.route('/api/analytics/status')
    def get_analytics_status():
        return jsonify({'enabled': False})

def run_web_server(host='0.0.0.0', port=5000, debug=False):
    """运行Web服务器"""
    logger.info(f"启动Web服务器: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    run_web_server(debug=True)
