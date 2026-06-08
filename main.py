"""
IMDB Top 250 监控主程序
"""
import time
import logging
import schedule
from datetime import datetime
from config import Config, setup_logging
from database import DatabaseManager
from hybrid_scraper import HybridScraper as IMDBScraper
from change_detector import ChangeDetector
from notifier import Notifier

# 设置日志
logger = setup_logging()

class IMDBMonitor:
    """IMDB Top 250 监控器"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = IMDBScraper()
        self.detector = ChangeDetector()
        self.notifier = Notifier()
        
        # 验证配置
        config_errors = Config.validate()
        if config_errors:
            for error in config_errors:
                logger.error(f"配置错误: {error}")
            raise ValueError("配置验证失败")
        
        logger.info("IMDB监控器初始化完成")
    
    def run_check(self):
        """执行一次检查"""
        try:
            logger.info("开始执行IMDB Top 250检查")
            
            # 1. 爬取最新数据
            new_data = self.scraper.fetch_top250()
            if not new_data:
                logger.error("爬取数据失败")
                return False
            
            # 2. 验证数据
            if not self.scraper.validate_data(new_data):
                logger.error("数据验证失败")
                return False
            
            # 3. 获取历史数据
            old_data = self.db.get_latest_data()
            
            # 4. 检测变化
            changes = self.detector.detect_changes(old_data, new_data)
            
            # 5. 保存新数据
            if not self.db.save_current_top250(new_data):
                logger.error("保存数据失败")
                return False
            
            # 6. 保存历史快照
            if not self.db.save_snapshot(new_data):
                logger.error("保存快照失败")
                return False
            
            # 7. 记录变化
            if changes['has_changes']:
                all_changes = (changes['rank_changes'] + 
                             changes['new_entries'] + 
                             changes['removed_entries'])
                if not self.db.record_changes(all_changes):
                    logger.error("记录变化失败")
            
            # 8. 发送通知
            if changes['has_changes']:
                notification_data = self.detector.format_changes_for_notification(changes)
                if not self.notifier.send_notification(notification_data):
                    logger.error("发送通知失败")
                    return False
                logger.info("通知发送成功")
            else:
                logger.info("没有检测到变化，跳过通知")
            
            logger.info("IMDB Top 250检查完成")
            return True
            
        except Exception as e:
            logger.error(f"执行检查时发生异常: {e}")
            return False
    
    def start_scheduler(self):
        """启动定时调度器"""
        logger.info(f"启动定时调度器，每天 {Config.SCHEDULE_TIME} 执行")
        
        # 设置定时任务
        schedule.every().day.at(Config.SCHEDULE_TIME).do(self.run_check)
        
        # 如果是首次运行且没有数据，立即执行一次
        if not self.db.has_data():
            logger.info("首次运行，立即执行一次检查")
            self.run_check()
        
        # 主循环
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止监控")
        except Exception as e:
            logger.error(f"调度器异常: {e}")
    
    def run_once(self):
        """手动执行一次检查"""
        logger.info("手动执行检查")
        return self.run_check()

def main():
    """主函数"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='IMDB Top 250 监控程序')
    parser.add_argument('--once', action='store_true', help='只运行一次，不启动调度器')
    parser.add_argument('--web', action='store_true', help='启动Web界面')
    parser.add_argument('--port', type=int, default=5000, help='Web服务器端口 (默认: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Web服务器主机 (默认: 0.0.0.0)')

    args = parser.parse_args()

    try:
        if args.web:
            # 启动Web界面
            logger.info(f"启动Web界面: http://{args.host}:{args.port}")
            from web_server import run_web_server
            run_web_server(host=args.host, port=args.port, debug=False)
        else:
            # 原有的命令行模式
            monitor = IMDBMonitor()

            if args.once:
                # 只执行一次
                success = monitor.run_once()
                sys.exit(0 if success else 1)
            else:
                # 启动定时调度
                monitor.start_scheduler()

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
