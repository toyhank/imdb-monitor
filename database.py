"""
数据库管理模块
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()

    def _serialize_json(self, data):
        """序列化数据为JSON字符串"""
        if data is None:
            return None
        try:
            import json
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return None

    def _deserialize_json(self, json_str):
        """反序列化JSON字符串"""
        if not json_str:
            return None
        try:
            import json
            return json.loads(json_str)
        except Exception:
            return None
    
    def init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建电影表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        imdb_id TEXT NOT NULL,
                        tmdb_id INTEGER,
                        title TEXT NOT NULL,
                        chinese_title TEXT,
                        year INTEGER,
                        rating REAL,
                        rank_position INTEGER NOT NULL,
                        directors TEXT,
                        countries TEXT,
                        genres TEXT,
                        overview TEXT,
                        poster_path TEXT,
                        runtime INTEGER,
                        tmdb_rating REAL,
                        vote_count INTEGER,
                        popularity REAL,
                        release_date TEXT,
                        original_language TEXT,
                        budget INTEGER,
                        revenue INTEGER,
                        cast TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建历史记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS movie_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        imdb_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        year INTEGER,
                        rating REAL,
                        rank_position INTEGER NOT NULL,
                        snapshot_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建变化记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS changes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        change_type TEXT NOT NULL,  -- 'rank_change', 'new_entry', 'removed'
                        imdb_id TEXT NOT NULL,
                        tmdb_id INTEGER,
                        title TEXT NOT NULL,
                        chinese_title TEXT,
                        year INTEGER,
                        rating REAL,
                        old_rank INTEGER,
                        new_rank INTEGER,
                        change_date DATE NOT NULL,
                        directors TEXT,
                        countries TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 动态检查并添加缺失的列（用于旧数据库升级）
                # movies 表升级
                movie_columns = [
                    ("tmdb_id", "INTEGER"), ("chinese_title", "TEXT"), ("directors", "TEXT"),
                    ("countries", "TEXT"), ("genres", "TEXT"), ("overview", "TEXT"),
                    ("poster_path", "TEXT"), ("runtime", "INTEGER"), ("tmdb_rating", "REAL"),
                    ("vote_count", "INTEGER"), ("popularity", "REAL"), ("release_date", "TEXT"),
                    ("original_language", "TEXT"), ("budget", "INTEGER"), ("revenue", "INTEGER"),
                    ("cast", "TEXT")
                ]
                for col_name, col_type in movie_columns:
                    try:
                        cursor.execute(f"ALTER TABLE movies ADD COLUMN {col_name} {col_type}")
                    except sqlite3.OperationalError:
                        pass

                # changes 表升级
                changes_columns = [
                    ("tmdb_id", "INTEGER"), ("chinese_title", "TEXT"), ("year", "INTEGER"),
                    ("rating", "REAL"), ("directors", "TEXT"), ("countries", "TEXT")
                ]
                for col_name, col_type in changes_columns:
                    try:
                        cursor.execute(f"ALTER TABLE changes ADD COLUMN {col_name} {col_type}")
                    except sqlite3.OperationalError:
                        pass

                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_imdb_id ON movies(imdb_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_rank ON movies(rank_position)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_date ON movie_history(snapshot_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_date ON changes(change_date)')
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def save_current_top250(self, movies: List[Dict]) -> bool:
        """保存当前Top 250数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 清空当前数据
                cursor.execute('DELETE FROM movies')
                
                # 插入新数据
                for movie in movies:
                    cursor.execute('''
                        INSERT INTO movies (
                            imdb_id, tmdb_id, title, chinese_title, year, rating, rank_position,
                            directors, countries, genres, overview, poster_path, runtime,
                            tmdb_rating, vote_count, popularity, release_date, original_language,
                            budget, revenue, cast
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        movie.get('imdb_id'),
                        movie.get('tmdb_id'),
                        movie['title'],
                        movie.get('chinese_title'),
                        movie['year'],
                        movie['rating'],
                        movie['rank'],
                        self._serialize_json(movie.get('directors')),
                        self._serialize_json(movie.get('countries')),
                        self._serialize_json(movie.get('genres')),
                        movie.get('overview'),
                        movie.get('poster_path'),
                        movie.get('runtime'),
                        movie.get('tmdb_rating'),
                        movie.get('vote_count'),
                        movie.get('popularity'),
                        movie.get('release_date'),
                        movie.get('original_language'),
                        movie.get('budget'),
                        movie.get('revenue'),
                        self._serialize_json(movie.get('cast'))
                    ))
                
                conn.commit()
                logger.info(f"保存了 {len(movies)} 部电影的数据")
                return True
                
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False
    
    def save_snapshot(self, movies: List[Dict], snapshot_date: str = None) -> bool:
        """保存历史快照"""
        if not snapshot_date:
            snapshot_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除同一天的旧快照
                cursor.execute('DELETE FROM movie_history WHERE snapshot_date = ?', (snapshot_date,))
                
                # 插入新快照
                for movie in movies:
                    cursor.execute('''
                        INSERT INTO movie_history (imdb_id, title, year, rating, rank_position, snapshot_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        movie['imdb_id'],
                        movie['title'],
                        movie['year'],
                        movie['rating'],
                        movie['rank'],
                        snapshot_date
                    ))
                
                conn.commit()
                logger.info(f"保存了 {snapshot_date} 的历史快照")
                return True
                
        except Exception as e:
            logger.error(f"保存快照失败: {e}")
            return False
    
    def get_latest_data(self) -> List[Dict]:
        """获取最新的Top 250数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM movies ORDER BY rank_position")

                # 获取列名
                column_names = [description[0] for description in cursor.description]

                movies = []
                for row in cursor.fetchall():
                    movie_dict = dict(zip(column_names, row))

                    # 添加显示标题
                    chinese_title = movie_dict.get('chinese_title')
                    title = movie_dict.get('title')
                    movie_dict['display_title'] = chinese_title or title

                    # 反序列化JSON字段
                    json_fields = ['directors', 'countries', 'genres', 'cast']
                    for field in json_fields:
                        if field in movie_dict:
                            movie_dict[field] = self._deserialize_json(movie_dict[field])

                    # 统一字段名
                    if 'rank_position' in movie_dict:
                        movie_dict['rank'] = movie_dict['rank_position']

                    movies.append(movie_dict)

                return movies

        except Exception as e:
            logger.error(f"获取最新数据失败: {e}")
            return []
    
    def record_changes(self, changes: List[Dict]) -> bool:
        """记录变化"""
        if not changes:
            return True
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                change_date = datetime.now().strftime('%Y-%m-%d')
                
                for change in changes:
                    cursor.execute('''
                        INSERT INTO changes (
                            change_type, imdb_id, tmdb_id, title, chinese_title, year, rating,
                            old_rank, new_rank, change_date, directors, countries
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        change['type'],
                        change.get('imdb_id'),
                        change.get('tmdb_id'),
                        change['title'],
                        change.get('chinese_title'),
                        change.get('year'),
                        change.get('rating'),
                        change.get('old_rank'),
                        change.get('new_rank'),
                        change_date,
                        self._serialize_json(change.get('directors')),
                        self._serialize_json(change.get('countries'))
                    ))
                
                conn.commit()
                logger.info(f"记录了 {len(changes)} 个变化")
                return True
                
        except Exception as e:
            logger.error(f"记录变化失败: {e}")
            return False

    def save_changes(self, changes: Dict) -> bool:
        """保存变化记录（别名方法，保持向后兼容）"""
        # 如果传入的是字典格式的changes，需要转换为列表格式
        if isinstance(changes, dict):
            change_list = []

            # 处理新增电影
            if changes.get('new_entries'):
                for entry in changes['new_entries']:
                    change_list.append({
                        'type': 'new',
                        'title': entry.get('title', ''),
                        'chinese_title': entry.get('chinese_title'),
                        'imdb_id': entry.get('imdb_id'),
                        'tmdb_id': entry.get('tmdb_id'),
                        'year': entry.get('year'),
                        'rating': entry.get('rating'),
                        'directors': entry.get('directors'),
                        'countries': entry.get('countries'),
                        'new_rank': entry.get('new_rank', entry.get('rank', 0)),
                        'old_rank': None
                    })

            # 处理移除电影
            if changes.get('removed_entries'):
                for entry in changes['removed_entries']:
                    change_list.append({
                        'type': 'removed',
                        'title': entry.get('title', ''),
                        'chinese_title': entry.get('chinese_title'),
                        'imdb_id': entry.get('imdb_id'),
                        'tmdb_id': entry.get('tmdb_id'),
                        'year': entry.get('year'),
                        'rating': entry.get('rating'),
                        'directors': entry.get('directors'),
                        'countries': entry.get('countries'),
                        'new_rank': None,
                        'old_rank': entry.get('old_rank', 0)
                    })

            # 处理排名变化
            if changes.get('rank_changes'):
                for entry in changes['rank_changes']:
                    change_list.append({
                        'type': 'rank_change',
                        'title': entry.get('title', ''),
                        'chinese_title': entry.get('chinese_title'),
                        'imdb_id': entry.get('imdb_id'),
                        'tmdb_id': entry.get('tmdb_id'),
                        'year': entry.get('year'),
                        'rating': entry.get('rating'),
                        'directors': entry.get('directors'),
                        'countries': entry.get('countries'),
                        'new_rank': entry.get('new_rank', 0),
                        'old_rank': entry.get('old_rank', 0)
                    })

            return self.record_changes(change_list)
        else:
            # 如果已经是列表格式，直接调用原方法
            return self.record_changes(changes)

    def save_data(self, movies: List[Dict]) -> bool:
        """保存数据（别名方法，保持向后兼容）"""
        return self.save_current_top250(movies)
    
    def has_data(self) -> bool:
        """检查是否有数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM movies')
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            logger.error(f"检查数据失败: {e}")
            return False
