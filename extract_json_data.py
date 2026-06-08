"""
从IMDB页面提取JSON数据
"""
import requests
import json
import re
from bs4 import BeautifulSoup
from config import Config

def extract_json_data():
    """提取页面中的JSON数据"""
    print("正在提取IMDB页面中的JSON数据...")
    
    session = requests.Session()
    session.headers.update({'User-Agent': Config.USER_AGENT})
    
    try:
        response = session.get(Config.IMDB_TOP250_URL, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找包含电影数据的script标签
        scripts = soup.find_all('script', type='application/ld+json')
        
        print(f"找到 {len(scripts)} 个JSON-LD脚本")
        
        for i, script in enumerate(scripts):
            try:
                data = json.loads(script.string)
                print(f"\nScript {i+1}:")
                print(f"类型: {data.get('@type', 'Unknown')}")
                
                if data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                    print(f"包含 {len(items)} 个项目")
                    
                    if items:
                        print("前5个项目:")
                        for j, item in enumerate(items[:5]):
                            movie = item.get('item', {})
                            name = movie.get('name', 'N/A')
                            url = movie.get('url', 'N/A')
                            print(f"  {j+1}. {name} - {url}")
                        
                        # 保存完整数据
                        with open('imdb_json_data.json', 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"完整JSON数据已保存到 imdb_json_data.json")
                        
                        return items
                        
            except json.JSONDecodeError as e:
                print(f"Script {i+1} JSON解析失败: {e}")
                continue
        
        # 查找其他可能包含数据的script标签
        print("\n查找其他script标签中的数据...")
        all_scripts = soup.find_all('script')
        
        for i, script in enumerate(all_scripts):
            if script.string and 'chartTitles' in script.string:
                print(f"\nScript {i} 包含 chartTitles:")
                content = script.string
                
                # 尝试提取JSON数据
                json_match = re.search(r'{"props".*}', content)
                if json_match:
                    try:
                        json_str = json_match.group(0)
                        data = json.loads(json_str)
                        
                        # 导航到电影数据
                        chart_titles = data.get('props', {}).get('pageProps', {}).get('pageData', {}).get('chartTitles', {})
                        edges = chart_titles.get('edges', [])
                        
                        print(f"找到 {len(edges)} 部电影")
                        
                        if edges:
                            print("前5部电影:")
                            movies = []
                            for edge in edges:
                                rank = edge.get('currentRank', 0)
                                node = edge.get('node', {})
                                title_text = node.get('titleText', {}).get('text', 'N/A')
                                release_year = node.get('releaseYear', {}).get('year', None)
                                rating = node.get('ratingsSummary', {}).get('aggregateRating', None)
                                imdb_id = node.get('id', 'N/A')
                                
                                movie_data = {
                                    'rank': rank,
                                    'title': title_text,
                                    'year': release_year,
                                    'rating': rating,
                                    'imdb_id': imdb_id
                                }
                                movies.append(movie_data)
                                
                                if len(movies) <= 5:
                                    print(f"  {rank}. {title_text} ({release_year}) - {rating}")
                            
                            # 保存电影数据
                            with open('imdb_movies_data.json', 'w', encoding='utf-8') as f:
                                json.dump(movies, f, indent=2, ensure_ascii=False)
                            print(f"\n电影数据已保存到 imdb_movies_data.json")
                            print(f"总共找到 {len(movies)} 部电影")
                            
                            return movies
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}")
                        # 保存原始内容用于调试
                        with open('imdb_script_content.txt', 'w', encoding='utf-8') as f:
                            f.write(content)
                        print("原始script内容已保存到 imdb_script_content.txt")
        
        return []
        
    except Exception as e:
        print(f"提取失败: {e}")
        return []

if __name__ == "__main__":
    movies = extract_json_data()
    if movies:
        print(f"\n成功提取 {len(movies)} 部电影数据")
    else:
        print("\n未能提取到电影数据")
