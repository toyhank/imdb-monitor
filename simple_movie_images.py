"""
简化版电影图片获取模块
使用公开的电影数据库API获取海报
"""
import base64
import hashlib
import logging
import requests
from io import BytesIO
from PIL import Image
from typing import Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class SimpleMovieImageFetcher:
    """简化版电影图片获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        })
        
        # 图片缓存
        self.image_cache = {}
        
        # 预定义的电影海报URL（用于演示）
        self.demo_posters = {
            'tt0111161': 'https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_SX300.jpg',  # The Shawshank Redemption
            'tt0068646': 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzAwMjU2MzY@._V1_SX300.jpg',  # The Godfather
            'tt0468569': 'https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg',  # The Dark Knight
            'tt0071562': 'https://m.media-amazon.com/images/M/MV5BMWMwMGQzZTItY2JlNC00OWZiLWIyMDctNDk2ZDQ2YjRjMWQ0XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',  # The Godfather Part II
            'tt0050083': 'https://m.media-amazon.com/images/M/MV5BMWU4N2FjNzYtNTVkNC00NzQ0LTg0MjAtYTJlMjFhNGUxZDFmXkEyXkFqcGdeQXVyNjc1NTYyMjg@._V1_SX300.jpg',  # 12 Angry Men
        }
    
    def get_movie_poster(self, imdb_id: str, title: str) -> Optional[Dict]:
        """获取电影海报"""
        try:
            # 检查缓存
            cache_key = f"{imdb_id}_{title}"
            if cache_key in self.image_cache:
                logger.debug(f"从缓存获取图片: {title}")
                return self.image_cache[cache_key]
            
            # 尝试从预定义URL获取
            poster_url = self.demo_posters.get(imdb_id)
            
            if not poster_url:
                # 尝试构建标准的IMDB海报URL
                poster_url = self._try_standard_poster_url(imdb_id)
            
            if poster_url:
                poster_data = self._download_and_process_image(poster_url, title)
                if poster_data:
                    # 缓存结果
                    self.image_cache[cache_key] = poster_data
                    logger.info(f"成功获取电影海报: {title}")
                    return poster_data
            
            logger.warning(f"未能获取电影海报: {title}")
            return None
            
        except Exception as e:
            logger.error(f"获取电影海报失败 {title}: {e}")
            return None
    
    def _try_standard_poster_url(self, imdb_id: str) -> Optional[str]:
        """尝试标准的IMDB海报URL格式"""
        # 这里可以尝试一些常见的IMDB图片URL格式
        # 但由于IMDB的反爬虫机制，这些可能不总是有效
        return None
    
    def _download_and_process_image(self, image_url: str, title: str) -> Optional[Dict]:
        """下载并处理图片"""
        try:
            logger.debug(f"下载图片: {image_url}")
            
            # 下载图片
            response = self.session.get(image_url, timeout=15)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"无效的图片类型: {content_type}")
                return None
            
            # 处理图片
            image_data = response.content
            
            # 压缩图片（企业微信有大小限制）
            processed_data = self._compress_image(image_data)
            
            if not processed_data:
                return None
            
            # 计算MD5
            md5_hash = hashlib.md5(processed_data).hexdigest()
            
            # 转换为base64
            base64_data = base64.b64encode(processed_data).decode('utf-8')
            
            return {
                'base64': base64_data,
                'md5': md5_hash,
                'size': len(processed_data),
                'url': image_url,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"下载处理图片失败 {title}: {e}")
            return None
    
    def _compress_image(self, image_data: bytes, max_size: int = 2 * 1024 * 1024) -> Optional[bytes]:
        """压缩图片"""
        try:
            # 如果图片已经足够小，直接返回
            if len(image_data) <= max_size:
                return image_data
            
            # 使用PIL压缩图片
            image = Image.open(BytesIO(image_data))
            
            # 转换为RGB（如果是RGBA）
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # 计算新尺寸
            width, height = image.size
            max_dimension = 600  # 最大尺寸
            
            if width > max_dimension or height > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * max_dimension / width)
                else:
                    new_height = max_dimension
                    new_width = int(width * max_dimension / height)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 保存为JPEG格式
            output = BytesIO()
            quality = 80
            
            while quality > 20:
                output.seek(0)
                output.truncate()
                image.save(output, format='JPEG', quality=quality, optimize=True)
                
                if output.tell() <= max_size:
                    break
                
                quality -= 10
            
            compressed_data = output.getvalue()
            
            logger.debug(f"图片压缩: {len(image_data)} -> {len(compressed_data)} bytes")
            return compressed_data
            
        except Exception as e:
            logger.error(f"图片压缩失败: {e}")
            return None
    
    def get_multiple_posters(self, movies: list, max_count: int = 3) -> Dict[str, Dict]:
        """批量获取多个电影海报"""
        posters = {}
        
        for i, movie in enumerate(movies[:max_count]):
            if i > 0:
                import time
                time.sleep(0.5)  # 避免请求过快
            
            imdb_id = movie.get('imdb_id')
            title = movie.get('title', 'Unknown')
            
            if imdb_id:
                poster = self.get_movie_poster(imdb_id, title)
                if poster:
                    posters[imdb_id] = poster
        
        return posters
    
    def clear_cache(self):
        """清空图片缓存"""
        self.image_cache.clear()
        logger.info("图片缓存已清空")
    
    def add_demo_poster(self, imdb_id: str, poster_url: str):
        """添加演示海报URL"""
        self.demo_posters[imdb_id] = poster_url
        logger.info(f"添加演示海报: {imdb_id} -> {poster_url}")

# 创建一个工厂函数来选择图片获取器
def create_image_fetcher():
    """创建图片获取器"""
    try:
        # 优先使用简化版
        return SimpleMovieImageFetcher()
    except Exception as e:
        logger.error(f"创建图片获取器失败: {e}")
        return None
