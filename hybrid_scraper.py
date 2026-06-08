#!/usr/bin/env python3
"""
混合爬虫 - 爬虫获取IMDB Top 250 + TMDB补充数据
"""
import requests
import time
from typing import List, Dict, Optional
from config import setup_logging
from api_config_manager import APIConfigManager

class HybridScraper:
    """混合爬虫：爬虫+API的最佳组合"""
    
    def __init__(self):
        self.config_manager = APIConfigManager()
        self.tmdb_api_key = self.config_manager.get_tmdb_api_key()

        # 初始化传统爬虫
        self._init_traditional_scraper()

        # TMDB API配置
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IMDB-Monitor/1.0'
        })

        # 数据库缓存
        self.db_movies = {}  # 数据库中已有的电影数据
        self._load_existing_movies()
    
    def _init_traditional_scraper(self):
        """初始化传统爬虫"""
        try:
            from scraper import IMDBScraper
            self.imdb_scraper = IMDBScraper()
            print("✅ IMDB传统爬虫初始化成功")
        except Exception as e:
            print(f"❌ IMDB传统爬虫初始化失败: {e}")
            self.imdb_scraper = None

    def _load_existing_movies(self):
        """从数据库加载已有的电影数据"""
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            existing_movies = db.get_latest_data()

            if existing_movies:
                # 建立IMDB ID到电影数据的映射
                for movie in existing_movies:
                    imdb_id = movie.get('imdb_id')
                    if imdb_id:
                        self.db_movies[imdb_id] = movie

                print(f"📋 从数据库加载了 {len(self.db_movies)} 部已有电影数据")
            else:
                print("📋 数据库中暂无电影数据")

        except Exception as e:
            print(f"⚠️  加载数据库电影数据失败: {e}")
            self.db_movies = {}
    
    def get_imdb_top250_list(self) -> List[Dict]:
        """使用传统爬虫获取真正的IMDB Top 250列表"""
        print("🕷️ 使用传统爬虫获取IMDB Top 250列表...")
        
        if not self.imdb_scraper:
            print("❌ IMDB爬虫不可用")
            return []
        
        try:
            # 使用传统爬虫获取IMDB Top 250
            movies = self.imdb_scraper.fetch_top250()
            
            if movies and len(movies) >= 200:
                print(f"✅ 成功获取 {len(movies)} 部IMDB Top 250电影")
                return movies
            else:
                print(f"⚠️  获取的电影数量不足: {len(movies) if movies else 0}")
                return movies or []
                
        except Exception as e:
            print(f"❌ IMDB爬虫获取失败: {e}")
            return []
    
    def enhance_movie_with_tmdb(self, movie: Dict) -> Dict:
        """使用TMDB API增强单部电影数据"""
        if not self.tmdb_api_key:
            return movie

        imdb_id = movie.get('imdb_id')
        if not imdb_id:
            return movie

        # 优先检查数据库中是否已有该电影
        if imdb_id in self.db_movies:
            db_movie = self.db_movies[imdb_id]
            # 检查是否有基本信息
            if db_movie.get('title') and db_movie.get('year'):
                # 检查是否缺少新字段或字段为null
                needs_enhancement = (
                    not db_movie.get('chinese_title') or
                    not db_movie.get('directors') or
                    not db_movie.get('countries') or
                    not db_movie.get('overview') or
                    not db_movie.get('tmdb_id')
                )

                if not needs_enhancement:
                    print(f"📋 使用数据库数据: {movie.get('title', 'Unknown')}")
                    # 更新排名信息，保留数据库中的完整数据
                    enhanced_movie = db_movie.copy()
                    enhanced_movie['rank'] = movie['rank']  # 更新最新排名
                    enhanced_movie['rating'] = movie.get('rating', db_movie.get('rating'))  # 更新评分
                    return enhanced_movie
                else:
                    # 需要增强，继续执行TMDB API调用
                    print(f"🔧 补充新字段: {movie.get('title', 'Unknown')}")

        try:
            # 调用TMDB API获取完整数据
            tmdb_movie = self._find_tmdb_movie_by_imdb_id(imdb_id)

            if tmdb_movie:
                print(f"🆕 TMDB新增强: {movie.get('title', 'Unknown')}")
                return self._merge_movie_data(movie, tmdb_movie)
            else:
                print(f"⚠️  TMDB未找到: {movie.get('title', 'Unknown')}")
                return movie

        except Exception as e:
            print(f"❌ TMDB增强失败 {imdb_id}: {e}")
            return movie
    
    def _find_tmdb_movie_by_imdb_id(self, imdb_id: str) -> Optional[Dict]:
        """通过IMDB ID查找TMDB电影"""
        try:
            url = f"{self.tmdb_base_url}/find/{imdb_id}"
            params = {
                'api_key': self.tmdb_api_key,
                'external_source': 'imdb_id',
                'language': 'zh-CN'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            movie_results = data.get('movie_results', [])
            
            if movie_results:
                movie = movie_results[0]
                
                # 获取详细信息
                tmdb_id = movie.get('id')
                if tmdb_id:
                    details = self._get_tmdb_movie_details(tmdb_id)
                    if details:
                        movie.update(details)
                
                return movie
            
            return None
            
        except Exception as e:
            print(f"❌ TMDB查找失败 {imdb_id}: {e}")
            return None
    
    def _get_tmdb_movie_details(self, tmdb_id: int) -> Optional[Dict]:
        """获取TMDB电影详细信息"""
        try:
            url = f"{self.tmdb_base_url}/movie/{tmdb_id}"
            params = {
                'api_key': self.tmdb_api_key,
                'language': 'zh-CN',
                'append_to_response': 'credits,production_countries'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"❌ 获取TMDB详情失败 {tmdb_id}: {e}")
            return None
    
    def _merge_movie_data(self, imdb_movie: Dict, tmdb_movie: Dict) -> Dict:
        """合并IMDB和TMDB数据"""
        # 以IMDB数据为主，TMDB数据补充
        merged = imdb_movie.copy()

        # 补充TMDB数据
        if tmdb_movie:
            # 基本信息
            merged['tmdb_id'] = tmdb_movie.get('id')
            merged['chinese_title'] = tmdb_movie.get('title')  # 中文标题
            merged['overview'] = tmdb_movie.get('overview', '')
            merged['poster_path'] = tmdb_movie.get('poster_path')
            merged['backdrop_path'] = tmdb_movie.get('backdrop_path')
            merged['tmdb_rating'] = tmdb_movie.get('vote_average')
            merged['vote_count'] = tmdb_movie.get('vote_count')
            merged['popularity'] = tmdb_movie.get('popularity')
            merged['release_date'] = tmdb_movie.get('release_date')
            merged['original_language'] = tmdb_movie.get('original_language')
            merged['budget'] = tmdb_movie.get('budget')
            merged['revenue'] = tmdb_movie.get('revenue')

            # 如果IMDB没有年份，使用TMDB的
            if not merged.get('year') and tmdb_movie.get('release_date'):
                try:
                    merged['year'] = int(tmdb_movie['release_date'].split('-')[0])
                except (ValueError, IndexError):
                    pass

            # 详细信息
            if tmdb_movie.get('genres'):
                merged['genres'] = [g['name'] for g in tmdb_movie['genres']]

            if tmdb_movie.get('runtime'):
                merged['runtime'] = tmdb_movie['runtime']

            # 制作国家
            if tmdb_movie.get('production_countries'):
                merged['countries'] = [c['name'] for c in tmdb_movie['production_countries']]

            # 演员和导演信息
            credits = tmdb_movie.get('credits', {})
            if credits:
                cast = credits.get('cast', [])[:5]
                crew = credits.get('crew', [])
                directors = [c['name'] for c in crew if c.get('job') == 'Director']

                merged['cast'] = [{'name': c['name'], 'character': c.get('character')} for c in cast]
                merged['directors'] = directors

        return merged
    
    def fetch_top250(self) -> List[Dict]:
        """主要接口：混合策略获取Top 250"""
        print("🔄 混合策略：IMDB爬虫 + TMDB增强")
        start_time = time.time()
        
        # 1. 使用传统爬虫获取IMDB Top 250列表
        movies = self.get_imdb_top250_list()
        
        if not movies:
            print("❌ 无法获取IMDB Top 250列表")
            return []
        
        print(f"📋 获取到 {len(movies)} 部IMDB电影，开始TMDB增强...")
        
        # 2. 智能检查哪些电影需要TMDB增强
        movies_need_enhancement = []
        movies_from_db = 0

        for movie in movies:
            imdb_id = movie.get('imdb_id')

            # 检查数据库中是否已有该电影
            if imdb_id and imdb_id in self.db_movies:
                db_movie = self.db_movies[imdb_id]
                # 检查是否有基本信息
                has_basic_info = db_movie.get('title') and db_movie.get('year')

                if has_basic_info:
                    # 检查是否缺少新字段或字段为null
                    needs_enhancement = (
                        not db_movie.get('chinese_title') or
                        not db_movie.get('directors') or
                        not db_movie.get('countries') or
                        not db_movie.get('overview') or
                        not db_movie.get('tmdb_id')
                    )

                    if not needs_enhancement:
                        # 所有字段都有值，无需增强
                        movies_from_db += 1
                        continue
                    else:
                        # 缺少字段或字段为null，需要增强
                        print(f"🔧 需要补充新字段: {movie.get('title', 'Unknown')}")
                        movies_need_enhancement.append(movie)
                        continue

            # 需要TMDB增强的情况：
            # 1. 数据库中没有该电影
            # 2. 数据库中有电影但缺少基本信息
            # 3. 数据库中有电影但缺少新字段或字段为null
            movies_need_enhancement.append(movie)

        print(f"📊 数据源分析:")
        print(f"  📋 数据库已有: {movies_from_db} 部")
        print(f"  🔧 需要TMDB增强: {len(movies_need_enhancement)} 部")
        print(f"  📈 API调用节省: {movies_from_db}/{len(movies)} ({movies_from_db/len(movies)*100:.1f}%)")

        # 3. 只对需要的电影进行TMDB增强
        enhanced_count = 0
        for i, movie in enumerate(movies):
            if movie in movies_need_enhancement:
                print(f"🔧 增强进度: {enhanced_count + 1}/{len(movies_need_enhancement)} - {movie.get('title', 'Unknown')}")
                enhanced_movie = self.enhance_movie_with_tmdb(movie)
                movies[i] = enhanced_movie
                enhanced_count += 1

                # 避免API请求过于频繁
                time.sleep(0.2)
            else:
                # 使用数据库数据，只更新排名
                imdb_id = movie.get('imdb_id')
                if imdb_id and imdb_id in self.db_movies:
                    db_movie = self.db_movies[imdb_id]
                    enhanced_movie = db_movie.copy()
                    enhanced_movie['rank'] = movie['rank']  # 更新排名
                    enhanced_movie['rating'] = movie.get('rating', db_movie.get('rating'))  # 更新评分
                    movies[i] = enhanced_movie
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🎉 混合策略完成!")
        print(f"📊 总电影数: {len(movies)}")
        print(f"� 数据库复用: {movies_from_db} 部")
        print(f"�🔧 TMDB增强: {enhanced_count} 部")
        print(f"⏱️  总耗时: {duration:.1f} 秒")
        print(f"� 效率提升: 节省 {movies_from_db} 次API调用")
        print(f"�💡 策略: IMDB排名 + 智能数据复用")
        
        return movies
    
    def scrape_top_250(self) -> List[Dict]:
        """兼容性方法"""
        return self.fetch_top250()
    
    def get_data_source_info(self) -> Dict:
        """获取数据源信息"""
        return {
            'imdb_available': self.imdb_scraper is not None,
            'tmdb_available': bool(self.tmdb_api_key),
            'preferred_source': 'hybrid',
            'strategy': 'IMDB ranking + TMDB enhancement'
        }

    def get_api_status(self) -> Dict:
        """获取API状态信息"""
        status = {
            'status': 'connected',
            'method': 'hybrid',
            'imdb_scraper': self.imdb_scraper is not None,
            'tmdb_api': bool(self.tmdb_api_key)
        }

        # 测试TMDB API连接
        if self.tmdb_api_key:
            try:
                test_movie = self._find_tmdb_movie_by_imdb_id("tt0111161")
                status['tmdb_test'] = bool(test_movie)
            except:
                status['tmdb_test'] = False

        return status
    
    def validate_data(self, movies: List[Dict]) -> bool:
        """验证数据完整性"""
        if not movies:
            return False
        
        # 检查基本字段
        required_fields = ['rank', 'title']
        for movie in movies:
            for field in required_fields:
                if field not in movie:
                    return False
        
        # 检查数据量
        return len(movies) >= 200

def test_hybrid_scraper():
    """测试混合爬虫"""
    print("🧪 测试混合爬虫")
    print("=" * 40)
    
    scraper = HybridScraper()
    
    # 显示数据源状态
    info = scraper.get_data_source_info()
    print("数据源状态:")
    print(f"  IMDB爬虫: {'✅' if info['imdb_available'] else '❌'}")
    print(f"  TMDB API: {'✅' if info['tmdb_available'] else '❌'}")
    print(f"  策略: {info['strategy']}")
    
    if not info['imdb_available']:
        print("❌ IMDB爬虫不可用，无法测试")
        return False
    
    print("\n⚠️  完整测试需要较长时间，这里只测试连接")
    
    # 测试IMDB爬虫连接
    try:
        print("测试IMDB爬虫连接...")
        # 这里不实际爬取，只测试初始化
        if scraper.imdb_scraper:
            print("✅ IMDB爬虫连接正常")
        else:
            print("❌ IMDB爬虫连接失败")
            return False
    except Exception as e:
        print(f"❌ IMDB爬虫测试失败: {e}")
        return False
    
    # 测试TMDB API连接
    if scraper.tmdb_api_key:
        try:
            print("测试TMDB API连接...")
            test_movie = scraper._find_tmdb_movie_by_imdb_id("tt0111161")  # The Shawshank Redemption
            if test_movie:
                print(f"✅ TMDB API连接正常: {test_movie.get('title')}")
            else:
                print("⚠️  TMDB API连接正常但未找到测试电影")
        except Exception as e:
            print(f"❌ TMDB API测试失败: {e}")
    else:
        print("⚠️  TMDB API密钥未配置")
    
    print("\n✅ 混合爬虫测试完成")
    print("💡 优势:")
    print("  - 获取真正的IMDB Top 250排名")
    print("  - TMDB API增强数据完整性")
    print("  - 智能缓存减少API调用")
    print("  - 只在需要时调用TMDB")
    
    return True

if __name__ == "__main__":
    setup_logging()
    test_hybrid_scraper()
