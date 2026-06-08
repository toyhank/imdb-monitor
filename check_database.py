"""
检查数据库状态
"""
from database import DatabaseManager
from datetime import datetime

def check_database_status():
    """检查数据库状态"""
    print("=== 数据库状态检查 ===")
    
    db = DatabaseManager()
    
    # 检查最新数据
    latest_data = db.get_latest_data()
    print(f"数据库中有 {len(latest_data)} 部电影")
    
    if latest_data:
        print("\n最新5部电影:")
        for i, movie in enumerate(latest_data[:5], 1):
            print(f"  {i}. {movie['title']} (#{movie['rank']})")
        
        print(f"\n最后5部电影:")
        for i, movie in enumerate(latest_data[-5:], len(latest_data)-4):
            print(f"  {i}. {movie['title']} (#{movie['rank']})")
    
    # 检查历史快照
    try:
        import sqlite3
        conn = sqlite3.connect('imdb_top250.db')
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT snapshot_date, COUNT(*) as movie_count FROM movie_history GROUP BY snapshot_date ORDER BY snapshot_date DESC")
        snapshots = cursor.fetchall()
        print(f"\n历史快照数量: {len(snapshots)}")

        if snapshots:
            print("最近的快照:")
            for date, count in snapshots[:5]:
                print(f"  {date}: {count} 部电影")

        conn.close()
    except Exception as e:
        print(f"检查历史快照时出错: {e}")
    
    # 检查变化记录
    try:
        # 获取最近的变化记录
        import sqlite3
        conn = sqlite3.connect('imdb_top250.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM changes")
        change_count = cursor.fetchone()[0]
        print(f"\n变化记录数量: {change_count}")
        
        if change_count > 0:
            cursor.execute("""
                SELECT change_date, change_type, COUNT(*) as count
                FROM changes
                GROUP BY change_date, change_type
                ORDER BY change_date DESC
                LIMIT 10
            """)
            recent_changes = cursor.fetchall()
            
            print("最近的变化:")
            for date, change_type, count in recent_changes:
                print(f"  {date} - {change_type}: {count} 个")
        
        conn.close()
        
    except Exception as e:
        print(f"检查变化记录时出错: {e}")

def check_latest_run():
    """检查最新运行情况"""
    print("\n=== 最新运行情况 ===")
    
    # 读取最新的日志
    try:
        with open('imdb_monitor.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找最近的成功运行
        recent_lines = lines[-20:]  # 最近20行
        
        print("最近的日志:")
        for line in recent_lines:
            if any(keyword in line for keyword in ['成功爬取', '数据验证通过', '保存了', '检查完成']):
                print(f"  {line.strip()}")
    
    except Exception as e:
        print(f"读取日志时出错: {e}")

if __name__ == "__main__":
    check_database_status()
    check_latest_run()
