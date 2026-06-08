#!/usr/bin/env python3
"""
API配置管理器
"""
import json
import os
from typing import Dict, Optional

class APIConfigManager:
    """API配置管理器"""
    
    def __init__(self, config_file: str = "api_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ 加载配置文件失败: {e}")
        
        # 返回默认配置
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "tmdb": {
                "api_key": "",
                "base_url": "https://api.themoviedb.org/3",
                "language": "zh-CN",
                "request_delay": 0.5,
                "timeout": 10
            },
            "omdb": {
                "api_key": "trilogy",
                "base_url": "http://www.omdbapi.com/"
            },
            "scraper": {
                "use_api": True,
                "preferred_api": "tmdb",
                "fallback_to_scraping": True
            }
        }
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False
    
    def get_tmdb_api_key(self) -> Optional[str]:
        """获取TMDB API密钥"""
        return self.config.get("tmdb", {}).get("api_key")
    
    def set_tmdb_api_key(self, api_key: str):
        """设置TMDB API密钥"""
        if "tmdb" not in self.config:
            self.config["tmdb"] = {}
        self.config["tmdb"]["api_key"] = api_key
        self.save_config()
    
    def get_omdb_api_key(self) -> Optional[str]:
        """获取OMDB API密钥"""
        return self.config.get("omdb", {}).get("api_key")
    
    def should_use_api(self) -> bool:
        """是否应该使用API而不是爬虫"""
        return self.config.get("scraper", {}).get("use_api", True)
    
    def get_preferred_api(self) -> str:
        """获取首选API"""
        return self.config.get("scraper", {}).get("preferred_api", "tmdb")

def setup_tmdb_api():
    """设置TMDB API"""
    print("🔧 TMDB API设置向导")
    print("=" * 30)
    
    config_manager = APIConfigManager()
    
    # 检查现有配置
    current_key = config_manager.get_tmdb_api_key()
    if current_key:
        print(f"当前API密钥: {current_key[:10]}...")
        use_current = input("是否使用当前密钥? (y/n): ").lower().strip()
        if use_current == 'y':
            return current_key
    
    # 获取新的API密钥
    print("\n📝 请输入你的TMDB API密钥:")
    print("   (可以在 https://www.themoviedb.org/settings/api 获取)")
    
    api_key = input("API密钥: ").strip()
    
    if not api_key:
        print("❌ API密钥不能为空")
        return None
    
    # 保存配置
    config_manager.set_tmdb_api_key(api_key)
    print("✅ API密钥已保存")
    
    return api_key

def main():
    """主函数"""
    print("⚙️ API配置管理器")
    print("=" * 30)
    
    config_manager = APIConfigManager()
    
    print("当前配置:")
    print(f"  TMDB API密钥: {'已配置' if config_manager.get_tmdb_api_key() else '未配置'}")
    print(f"  OMDB API密钥: {'已配置' if config_manager.get_omdb_api_key() else '未配置'}")
    print(f"  使用API: {'是' if config_manager.should_use_api() else '否'}")
    print(f"  首选API: {config_manager.get_preferred_api()}")
    
    # 设置TMDB API
    setup_tmdb_api()

if __name__ == "__main__":
    main()
