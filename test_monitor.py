"""
测试脚本
"""
import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from database import DatabaseManager
from change_detector import ChangeDetector
from scraper import IMDBScraper
from notifier import Notifier

class TestDatabaseManager(unittest.TestCase):
    """测试数据库管理器"""
    
    def setUp(self):
        # 使用临时文件作为测试数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        # 清理临时文件
        try:
            # 确保数据库连接已关闭
            if hasattr(self.db, '_connection'):
                self.db._connection.close()
            os.unlink(self.temp_db.name)
        except (OSError, PermissionError):
            # 在Windows上可能会有文件锁定问题，忽略清理错误
            pass
    
    def test_init_database(self):
        """测试数据库初始化"""
        # 数据库应该已经初始化
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_and_get_data(self):
        """测试保存和获取数据"""
        test_movies = [
            {
                'imdb_id': 'tt0111161',
                'title': 'The Shawshank Redemption',
                'year': 1994,
                'rating': 9.3,
                'rank': 1
            },
            {
                'imdb_id': 'tt0068646',
                'title': 'The Godfather',
                'year': 1972,
                'rating': 9.2,
                'rank': 2
            }
        ]
        
        # 保存数据
        result = self.db.save_current_top250(test_movies)
        self.assertTrue(result)
        
        # 获取数据
        retrieved_data = self.db.get_latest_data()
        self.assertEqual(len(retrieved_data), 2)
        self.assertEqual(retrieved_data[0]['title'], 'The Shawshank Redemption')
    
    def test_has_data(self):
        """测试数据存在检查"""
        # 初始应该没有数据
        self.assertFalse(self.db.has_data())
        
        # 添加数据后应该有数据
        test_movies = [{'imdb_id': 'tt0111161', 'title': 'Test', 'year': 2000, 'rating': 8.0, 'rank': 1}]
        self.db.save_current_top250(test_movies)
        self.assertTrue(self.db.has_data())

class TestChangeDetector(unittest.TestCase):
    """测试变化检测器"""
    
    def setUp(self):
        self.detector = ChangeDetector()
    
    def test_no_old_data(self):
        """测试没有历史数据的情况"""
        new_data = [{'imdb_id': 'tt0111161', 'title': 'Test', 'rank': 1}]
        changes = self.detector.detect_changes([], new_data)
        
        self.assertFalse(changes['has_changes'])
        self.assertEqual(changes['summary'], "首次运行，建立基准数据")
    
    def test_rank_changes(self):
        """测试排名变化检测"""
        old_data = [
            {'imdb_id': 'tt0111161', 'title': 'Movie A', 'rank': 1},
            {'imdb_id': 'tt0068646', 'title': 'Movie B', 'rank': 2}
        ]
        new_data = [
            {'imdb_id': 'tt0068646', 'title': 'Movie B', 'rank': 1},
            {'imdb_id': 'tt0111161', 'title': 'Movie A', 'rank': 2}
        ]
        
        changes = self.detector.detect_changes(old_data, new_data)
        
        self.assertTrue(changes['has_changes'])
        self.assertEqual(len(changes['rank_changes']), 2)
    
    def test_new_entries(self):
        """测试新增电影检测"""
        old_data = [{'imdb_id': 'tt0111161', 'title': 'Movie A', 'rank': 1}]
        new_data = [
            {'imdb_id': 'tt0111161', 'title': 'Movie A', 'rank': 1},
            {'imdb_id': 'tt0068646', 'title': 'Movie B', 'rank': 2}
        ]
        
        changes = self.detector.detect_changes(old_data, new_data)
        
        self.assertTrue(changes['has_changes'])
        self.assertEqual(len(changes['new_entries']), 1)
        self.assertEqual(changes['new_entries'][0]['title'], 'Movie B')
    
    def test_removed_entries(self):
        """测试移除电影检测"""
        old_data = [
            {'imdb_id': 'tt0111161', 'title': 'Movie A', 'rank': 1},
            {'imdb_id': 'tt0068646', 'title': 'Movie B', 'rank': 2}
        ]
        new_data = [{'imdb_id': 'tt0111161', 'title': 'Movie A', 'rank': 1}]
        
        changes = self.detector.detect_changes(old_data, new_data)
        
        self.assertTrue(changes['has_changes'])
        self.assertEqual(len(changes['removed_entries']), 1)
        self.assertEqual(changes['removed_entries'][0]['title'], 'Movie B')

class TestIMDBScraper(unittest.TestCase):
    """测试IMDB爬虫"""
    
    def setUp(self):
        self.scraper = IMDBScraper()
    
    def test_validate_data_empty(self):
        """测试空数据验证"""
        self.assertFalse(self.scraper.validate_data([]))
    
    def test_validate_data_insufficient(self):
        """测试数据不足验证"""
        movies = [{'rank': i, 'title': f'Movie {i}', 'imdb_id': f'tt{i:07d}'} for i in range(1, 50)]
        self.assertFalse(self.scraper.validate_data(movies))
    
    def test_validate_data_missing_fields(self):
        """测试缺少字段验证"""
        movies = [{'rank': 1, 'title': 'Movie 1'}]  # 缺少imdb_id
        self.assertFalse(self.scraper.validate_data(movies))
    
    def test_validate_data_valid(self):
        """测试有效数据验证"""
        movies = [
            {'rank': i, 'title': f'Movie {i}', 'imdb_id': f'tt{i:07d}'}
            for i in range(1, 251)
        ]
        self.assertTrue(self.scraper.validate_data(movies))

class TestNotifier(unittest.TestCase):
    """测试通知发送器"""
    
    def setUp(self):
        self.notifier = Notifier()
    
    @patch('notifier.requests.post')
    def test_send_webhook_success(self, mock_post):
        """测试Webhook发送成功"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # 模拟配置
        with patch.object(self.notifier.config, 'WEBHOOK_URL', 'http://test.com'):
            with patch.object(self.notifier.config, 'NOTIFICATION_TYPE', 'webhook'):
                notification_data = {
                    'message': 'Test message',
                    'details': {
                        'timestamp': '2023-01-01T00:00:00',
                        'summary': 'Test summary'
                    }
                }
                
                result = self.notifier.send_notification(notification_data)
                self.assertTrue(result)
                mock_post.assert_called_once()
    
    def test_send_notification_no_changes(self):
        """测试没有变化时的通知"""
        notification_data = {
            'message': 'No changes',
            'details': None
        }
        
        result = self.notifier.send_notification(notification_data)
        self.assertTrue(result)

def run_tests():
    """运行所有测试"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_tests()
