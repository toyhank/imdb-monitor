"""
变化检测模块
"""
import logging
from typing import List, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ChangeDetector:
    """变化检测器"""
    
    def __init__(self):
        pass
    
    def detect_changes(self, old_data: List[Dict], new_data: List[Dict]) -> Dict:
        """检测变化"""
        if not old_data:
            logger.info("没有历史数据，跳过变化检测")
            return {
                'rank_changes': [],
                'new_entries': [],
                'removed_entries': [],
                'has_changes': False,
                'summary': "首次运行，建立基准数据"
            }
        
        logger.info("开始检测变化")
        
        # 创建查找字典
        old_dict = {movie['imdb_id']: movie for movie in old_data}
        new_dict = {movie['imdb_id']: movie for movie in new_data}
        
        # 检测各种变化
        rank_changes = self._detect_rank_changes(old_dict, new_dict)
        new_entries = self._detect_new_entries(old_dict, new_dict)
        removed_entries = self._detect_removed_entries(old_dict, new_dict)
        
        has_changes = bool(rank_changes or new_entries or removed_entries)
        
        # 生成摘要
        summary = self._generate_summary(rank_changes, new_entries, removed_entries)
        
        result = {
            'rank_changes': rank_changes,
            'new_entries': new_entries,
            'removed_entries': removed_entries,
            'has_changes': has_changes,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"变化检测完成: {summary}")
        return result
    
    def _detect_rank_changes(self, old_dict: Dict, new_dict: Dict) -> List[Dict]:
        """检测排名变化"""
        rank_changes = []
        
        for imdb_id, new_movie in new_dict.items():
            if imdb_id in old_dict:
                old_movie = old_dict[imdb_id]
                old_rank = old_movie['rank']
                new_rank = new_movie['rank']
                
                if old_rank != new_rank:
                    change = {
                        'type': 'rank_change',
                        'imdb_id': imdb_id,
                        'title': new_movie['title'],
                        'chinese_title': new_movie.get('chinese_title'),
                        'display_title': new_movie.get('chinese_title') or new_movie['title'],
                        'old_rank': old_rank,
                        'new_rank': new_rank,
                        'rank_diff': old_rank - new_rank,  # 正数表示上升
                        'year': new_movie.get('year'),
                        'rating': new_movie.get('rating'),
                        'directors': new_movie.get('directors'),
                        'countries': new_movie.get('countries')
                    }
                    rank_changes.append(change)
        
        # 按排名变化幅度排序
        rank_changes.sort(key=lambda x: abs(x['rank_diff']), reverse=True)
        return rank_changes
    
    def _detect_new_entries(self, old_dict: Dict, new_dict: Dict) -> List[Dict]:
        """检测新增电影"""
        new_entries = []
        
        for imdb_id, movie in new_dict.items():
            if imdb_id not in old_dict:
                entry = {
                    'type': 'new_entry',
                    'imdb_id': imdb_id,
                    'title': movie['title'],
                    'chinese_title': movie.get('chinese_title'),
                    'display_title': movie.get('chinese_title') or movie['title'],
                    'new_rank': movie['rank'],
                    'year': movie.get('year'),
                    'rating': movie.get('rating'),
                    'directors': movie.get('directors'),
                    'countries': movie.get('countries')
                }
                new_entries.append(entry)
        
        # 按排名排序
        new_entries.sort(key=lambda x: x['new_rank'])
        return new_entries
    
    def _detect_removed_entries(self, old_dict: Dict, new_dict: Dict) -> List[Dict]:
        """检测移除的电影"""
        removed_entries = []
        
        for imdb_id, movie in old_dict.items():
            if imdb_id not in new_dict:
                entry = {
                    'type': 'removed',
                    'imdb_id': imdb_id,
                    'title': movie['title'],
                    'chinese_title': movie.get('chinese_title'),
                    'display_title': movie.get('chinese_title') or movie['title'],
                    'old_rank': movie['rank'],
                    'year': movie.get('year'),
                    'rating': movie.get('rating'),
                    'directors': movie.get('directors'),
                    'countries': movie.get('countries')
                }
                removed_entries.append(entry)
        
        # 按原排名排序
        removed_entries.sort(key=lambda x: x['old_rank'])
        return removed_entries
    
    def _generate_summary(self, rank_changes: List[Dict], new_entries: List[Dict], 
                         removed_entries: List[Dict]) -> str:
        """生成变化摘要"""
        if not (rank_changes or new_entries or removed_entries):
            return "没有检测到变化"
        
        summary_parts = []
        
        if rank_changes:
            summary_parts.append(f"{len(rank_changes)}部电影排名发生变化")
            
            # 找出最大的上升和下降
            biggest_rise = max(rank_changes, key=lambda x: x['rank_diff'], default=None)
            biggest_fall = min(rank_changes, key=lambda x: x['rank_diff'], default=None)
            
            if biggest_rise and biggest_rise['rank_diff'] > 0:
                summary_parts.append(f"最大上升: {biggest_rise.get('display_title') or biggest_rise['title']} (#{biggest_rise['old_rank']} → #{biggest_rise['new_rank']})")
            
            if biggest_fall and biggest_fall['rank_diff'] < 0:
                summary_parts.append(f"最大下降: {biggest_fall.get('display_title') or biggest_fall['title']} (#{biggest_fall['old_rank']} → #{biggest_fall['new_rank']})")
        
        if new_entries:
            summary_parts.append(f"{len(new_entries)}部新电影进入榜单")
            if new_entries:
                highest_new = min(new_entries, key=lambda x: x['new_rank'])
                summary_parts.append(f"最高新进: {highest_new.get('display_title') or highest_new['title']} (#{highest_new['new_rank']})")
        
        if removed_entries:
            summary_parts.append(f"{len(removed_entries)}部电影离开榜单")
            if removed_entries:
                highest_removed = min(removed_entries, key=lambda x: x['old_rank'])
                summary_parts.append(f"最高离开: {highest_removed.get('display_title') or highest_removed['title']} (原#{highest_removed['old_rank']})")
        
        return "; ".join(summary_parts)
    
    def format_changes_for_notification(self, changes: Dict) -> Dict:
        """格式化变化数据用于通知"""
        if not changes['has_changes']:
            return {
                'message': changes['summary'],
                'details': None
            }
        
        # 构建详细信息
        details = {
            'timestamp': changes['timestamp'],
            'summary': changes['summary']
        }
        
        if changes['rank_changes']:
            details['rank_changes'] = [
                {
                    'title': change.get('display_title') or change['title'],
                    'display_title': change.get('display_title'),
                    'chinese_title': change.get('chinese_title'),
                    'old_rank': change['old_rank'],
                    'new_rank': change['new_rank'],
                    'change': f"{'↑' if change['rank_diff'] > 0 else '↓'}{abs(change['rank_diff'])}",
                    'year': change.get('year'),
                    'rating': change.get('rating'),
                    'imdb_id': change.get('imdb_id')
                }
                for change in changes['rank_changes'][:10]  # 只显示前10个
            ]
        
        if changes['new_entries']:
            details['new_entries'] = [
                {
                    'title': entry.get('display_title') or entry['title'],
                    'display_title': entry.get('display_title'),
                    'chinese_title': entry.get('chinese_title'),
                    'rank': entry['new_rank'],
                    'year': entry.get('year'),
                    'rating': entry.get('rating'),
                    'imdb_id': entry.get('imdb_id')
                }
                for entry in changes['new_entries']
            ]
        
        if changes['removed_entries']:
            details['removed_entries'] = [
                {
                    'title': entry.get('display_title') or entry['title'],
                    'display_title': entry.get('display_title'),
                    'chinese_title': entry.get('chinese_title'),
                    'old_rank': entry['old_rank'],
                    'year': entry.get('year'),
                    'rating': entry.get('rating'),
                    'imdb_id': entry.get('imdb_id')
                }
                for entry in changes['removed_entries']
            ]
        
        return {
            'message': f"IMDB Top 250 变化检测 - {changes['summary']}",
            'details': details
        }
