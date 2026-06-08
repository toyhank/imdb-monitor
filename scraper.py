"""
IMDB Top 250 爬虫模块
"""
import re
import time
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from config import Config

logger = logging.getLogger(__name__)

class IMDBScraper:
    """IMDB Top 250 爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def fetch_top250(self) -> List[Dict]:
        """获取IMDB Top 250数据"""
        try:
            logger.info(f"开始爬取IMDB Top 250数据 from {Config.IMDB_TOP250_URL}")

            # 发送请求
            response = self.session.get(Config.IMDB_TOP250_URL, timeout=30)
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the movie list table (Table 1 is the 250 movie list)
            tables = soup.find_all('table')
            if len(tables) < 2:
                logger.error("未找到电影列表表格")
                return []
                
            table = tables[1]
            rows = table.find_all('tr')[1:] # Skip header
            
            movies = []
            for idx, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) < 5:
                    logger.warning(f"跳过格式不合规的行 {idx}: {row.text.strip()}")
                    continue
                    
                # 1. Rank
                try:
                    rank = int(cols[0].text.strip())
                except ValueError:
                    rank = idx
                
                # 2. Movie link & Title/Year info
                link_elem = cols[2].find('a')
                if not link_elem:
                    logger.warning(f"第 {idx} 行未找到电影链接")
                    continue
                    
                href = link_elem.get('href', '')
                # Extract ID
                id_match = re.search(r'\?(\d+)', href)
                if not id_match:
                    logger.warning(f"第 {idx} 行链接格式不正确: {href}")
                    continue
                    
                imdb_num = id_match.group(1)
                imdb_id = f"tt{imdb_num.zfill(7)}"
                
                # Title and Year
                full_text = link_elem.text.strip()
                text_match = re.search(r'^(.*?)\s*\((\d{4})\)$', full_text)
                if text_match:
                    title = text_match.group(1).strip()
                    year = int(text_match.group(2))
                else:
                    title = full_text
                    year = None
                    
                # 3. Rating
                try:
                    rating = float(cols[3].text.strip())
                except ValueError:
                    rating = None
                    
                movies.append({
                    'rank': rank,
                    'title': title,
                    'year': year,
                    'rating': rating,
                    'imdb_id': imdb_id
                })
                
            logger.info(f"成功爬取 {len(movies)} 部电影数据")
            
            # 添加延迟避免被限制
            time.sleep(Config.REQUEST_DELAY)
            
            return movies

        except requests.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"爬取数据失败: {e}")
            return []

    def scrape_top_250(self) -> List[Dict]:
        """获取IMDB Top 250数据（别名方法，保持向后兼容）"""
        return self.fetch_top250()

    def validate_data(self, movies: List[Dict]) -> bool:
        """验证爬取的数据"""
        if not movies:
            logger.error("没有爬取到任何数据")
            return False

        min_count = Config.MIN_MOVIES_COUNT
        if len(movies) < min_count:  # 检查最少电影数量
            logger.warning(f"爬取的电影数量异常: {len(movies)}")
            return False
        
        # 检查必要字段
        required_fields = ['rank', 'title', 'imdb_id']
        for movie in movies[:10]:  # 检查前10部
            for field in required_fields:
                if field not in movie or not movie[field]:
                    logger.error(f"电影数据缺少必要字段: {field}")
                    return False
        
        logger.info("数据验证通过")
        return True
