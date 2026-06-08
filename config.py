"""
配置管理模块
"""
import os
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config.env')

class Config:
    """配置类"""
    
    # 通知设置
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    NOTIFICATION_TYPE = os.getenv('NOTIFICATION_TYPE', 'webhook')  # webhook, email, both, wechat_clawbot
    WEBHOOK_TYPE = os.getenv('WEBHOOK_TYPE', 'wework')  # wework, slack, generic
    ENABLE_MOVIE_IMAGES = os.getenv('ENABLE_MOVIE_IMAGES', 'true').lower() == 'true'
    WECHAT_CLAWBOT_PUSH_URL = os.getenv('WECHAT_CLAWBOT_PUSH_URL', 'http://127.0.0.1:5001/send')
    
    # 邮件设置
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_TO = os.getenv('EMAIL_TO', '')
    
    # 爬取设置
    USER_AGENT = os.getenv('USER_AGENT',
                          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '1'))
    MIN_MOVIES_COUNT = int(os.getenv('MIN_MOVIES_COUNT', '200'))
    
    # 调度设置
    SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '09:00')
    
    # 数据库设置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'imdb_top250.db')
    
    # 日志设置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'imdb_monitor.log')
    
    # IMDB URL
    IMDB_TOP250_URL = 'http://top250.info/charts/'

    # Google Analytics设置
    GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '')
    ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true'
    SHOW_ANALYTICS_UI = os.getenv('SHOW_ANALYTICS_UI', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """验证配置"""
        errors = []
        
        if cls.NOTIFICATION_TYPE in ['webhook', 'both'] and not cls.WEBHOOK_URL:
            errors.append("WEBHOOK_URL is required when using webhook notification")
            
        if cls.NOTIFICATION_TYPE in ['email', 'both']:
            if not all([cls.EMAIL_USERNAME, cls.EMAIL_PASSWORD, cls.EMAIL_TO]):
                errors.append("Email configuration is incomplete")
        
        return errors

def setup_logging():
    """设置日志"""
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 设置根日志器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 文件处理器
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
