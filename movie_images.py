"""
电影图片获取模块
"""
import re
import time
import base64
import hashlib
import logging
import requests
from io import BytesIO
from PIL import Image
from typing import Dict, Optional, Tuple
from config import Config

logger = logging.getLogger(__name__)

class MovieImageFetcher:
    """电影图片获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # 图片缓存
        self.image_cache = {}
    
    def get_movie_poster(self, imdb_id: str, title: str) -> Optional[Dict]:
        """获取电影海报"""
        try:
            # 检查缓存
            cache_key = f"{imdb_id}_{title}"
            if cache_key in self.image_cache:
                logger.debug(f"从缓存获取图片: {title}")
                return self.image_cache[cache_key]
            
            # 从IMDB获取海报
            poster_data = self._fetch_imdb_poster(imdb_id, title)
            
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
    
    def _fetch_imdb_poster(self, imdb_id: str, title: str) -> Optional[Dict]:
        """从IMDB获取海报"""
        try:
            # 构建IMDB电影页面URL
            movie_url = f"https://www.imdb.com/title/{imdb_id}/"
            
            logger.debug(f"获取电影页面: {movie_url}")
            response = self.session.get(movie_url, timeout=10)
            response.raise_for_status()
            
            # 查找海报图片URL
            poster_url = self._extract_poster_url(response.text)
            
            if not poster_url:
                logger.warning(f"未在页面中找到海报URL: {title}")
                return None
            
            # 下载并处理图片
            return self._download_and_process_image(poster_url, title)
            
        except Exception as e:
            logger.error(f"从IMDB获取海报失败 {title}: {e}")
            return None
    
    def _extract_poster_url(self, html_content: str) -> Optional[str]:
        """从HTML中提取海报URL"""
        try:
            # 查找海报图片的多种模式
            patterns = [
                # 新版IMDB页面模式
                r'"image":"([^"]*\.jpg[^"]*)"',  # JSON-LD中的图片
                r'"url":"([^"]*\.jpg[^"]*)"[^}]*"@type":"ImageObject"',  # ImageObject类型
                r'<img[^>]*class="[^"]*ipc-image[^"]*"[^>]*src="([^"]*)"',  # ipc-image类
                r'<img[^>]*src="([^"]*)"[^>]*class="[^"]*ipc-image[^"]*"',  # 另一种ipc-image格式

                # 传统模式
                r'<img[^>]*class="[^"]*poster[^"]*"[^>]*src="([^"]*)"',  # poster类的img标签
                r'<img[^>]*src="([^"]*)"[^>]*class="[^"]*poster[^"]*"',  # 另一种poster格式
                r'"poster":{"url":"([^"]*)"',  # poster对象中的URL
                r'<meta property="og:image" content="([^"]*)"',  # Open Graph图片

                # 备用模式
                r'src="([^"]*\.jpg[^"]*)"[^>]*alt="[^"]*poster[^"]*"',  # alt包含poster的图片
                r'data-src="([^"]*\.jpg[^"]*)"',  # 懒加载图片
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    # 清理URL
                    url = match.replace('\\', '')
                    if self._is_valid_image_url(url):
                        logger.debug(f"找到海报URL: {url}")
                        return url

            # 如果没找到，尝试使用默认的IMDB图片URL格式
            return self._try_default_poster_url(html_content)

        except Exception as e:
            logger.error(f"提取海报URL失败: {e}")
            return None

    def _try_default_poster_url(self, html_content: str) -> Optional[str]:
        """尝试使用默认的IMDB海报URL格式"""
        try:
            # 查找任何包含IMDB图片域名的URL
            imdb_image_patterns = [
                r'(https://m\.media-amazon\.com/images/M/[^"]*\.jpg[^"]*)',
                r'(https://images-na\.ssl-images-amazon\.com/images/M/[^"]*\.jpg[^"]*)',
            ]

            for pattern in imdb_image_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    if self._is_valid_image_url(match):
                        logger.debug(f"找到默认格式海报URL: {match}")
                        return match

            return None

        except Exception as e:
            logger.error(f"尝试默认海报URL失败: {e}")
            return None
    
    def _is_valid_image_url(self, url: str) -> bool:
        """验证图片URL是否有效"""
        if not url or len(url) < 10:
            return False
        
        # 检查是否是图片URL
        if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return False
        
        # 检查是否是IMDB的图片
        if 'imdb.com' not in url and 'amazonaws.com' not in url:
            return False
        
        return True
    
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
            max_dimension = 800  # 最大尺寸
            
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
            quality = 85
            
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
                time.sleep(1)  # 避免请求过快
            
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
