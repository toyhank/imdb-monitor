"""
调试IMDB爬虫 - 分析页面结构
"""
import requests
from bs4 import BeautifulSoup
import re
from config import Config

def analyze_page_structure():
    """分析IMDB Top 250页面结构"""
    print("正在分析IMDB Top 250页面结构...")
    
    # 发送请求
    session = requests.Session()
    session.headers.update({
        'User-Agent': Config.USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    try:
        response = session.get(Config.IMDB_TOP250_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"页面标题: {soup.title.string if soup.title else 'N/A'}")
        print(f"页面大小: {len(response.content)} bytes")
        
        # 查找各种可能的选择器
        selectors_to_test = [
            ('li.ipc-metadata-list-summary-item', '新版列表项'),
            ('tr.titleColumn', '旧版表格行'),
            ('li.titleColumn', '列表项标题列'),
            ('div.titleColumn', 'div标题列'),
            ('li[class*="list"]', '包含list的li'),
            ('li[class*="item"]', '包含item的li'),
            ('li[class*="summary"]', '包含summary的li'),
            ('div[class*="list"]', '包含list的div'),
            ('article', 'article标签'),
            ('li', '所有li标签'),
            ('tr', '所有tr标签'),
        ]
        
        for selector, description in selectors_to_test:
            elements = soup.select(selector)
            print(f"\n{description} ({selector}): 找到 {len(elements)} 个元素")
            
            if elements and len(elements) > 10:  # 如果找到较多元素，显示前几个的结构
                print("前3个元素的类名:")
                for i, elem in enumerate(elements[:3]):
                    classes = elem.get('class', [])
                    print(f"  {i+1}. {' '.join(classes) if classes else '无类名'}")
                    
                    # 查找标题
                    title_candidates = [
                        elem.find('h3'),
                        elem.find('a'),
                        elem.find('span', class_=lambda x: x and 'title' in x.lower()),
                        elem.find(text=re.compile(r'^\d+\.')),
                    ]
                    
                    for candidate in title_candidates:
                        if candidate:
                            text = candidate.get_text(strip=True) if hasattr(candidate, 'get_text') else str(candidate).strip()
                            if text and len(text) > 5:
                                print(f"     可能的标题: {text[:50]}...")
                                break
        
        # 查找包含电影标题的文本
        print("\n查找包含已知电影标题的元素:")
        known_titles = ["Shawshank", "Godfather", "Dark Knight"]
        
        for title in known_titles:
            elements = soup.find_all(text=re.compile(title, re.IGNORECASE))
            print(f"包含 '{title}' 的文本: {len(elements)} 个")
            
            for elem in elements[:2]:  # 只显示前2个
                parent = elem.parent if elem.parent else None
                if parent:
                    print(f"  父元素: {parent.name} class={parent.get('class', [])}")
                    print(f"  文本: {str(elem).strip()[:100]}...")
        
        # 查找JSON数据
        print("\n查找页面中的JSON数据:")
        scripts = soup.find_all('script')
        for i, script in enumerate(scripts):
            if script.string and ('top' in script.string.lower() or 'movie' in script.string.lower()):
                content = script.string[:200]
                print(f"Script {i}: {content}...")
        
        # 保存页面内容用于进一步分析
        with open('imdb_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"\n页面内容已保存到 imdb_page_debug.html")

    except Exception as e:
        print(f"分析失败: {e}")

def test_alternative_selectors():
    """测试替代选择器"""
    print("\n=== 测试替代选择器 ===")
    
    session = requests.Session()
    session.headers.update({'User-Agent': Config.USER_AGENT})
    
    try:
        response = session.get(Config.IMDB_TOP250_URL, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 更广泛的选择器测试
        alternative_selectors = [
            'li[data-testid]',
            'div[data-testid]',
            '[data-testid*="title"]',
            '[data-testid*="list"]',
            'li.cli-item',
            'div.cli-item',
            'li.ipc-title',
            'div.ipc-title',
            'h3.ipc-title__text',
            'a[href*="/title/tt"]',
        ]
        
        for selector in alternative_selectors:
            elements = soup.select(selector)
            print(f"{selector}: {len(elements)} 个元素")
            
            if elements:
                # 检查前几个元素是否包含电影信息
                for i, elem in enumerate(elements[:3]):
                    text = elem.get_text(strip=True)
                    if any(title in text for title in ["Shawshank", "Godfather", "Dark Knight"]):
                        print(f"  ✓ 元素 {i+1} 包含已知电影: {text[:50]}...")
                        
                        # 分析这个元素的结构
                        print(f"    标签: {elem.name}")
                        print(f"    类名: {elem.get('class', [])}")
                        print(f"    属性: {dict(elem.attrs)}")
                        
                        # 查找链接
                        link = elem.find('a', href=True) or (elem if elem.name == 'a' and elem.get('href') else None)
                        if link:
                            href = link.get('href', '')
                            if '/title/tt' in href:
                                print(f"    IMDB链接: {href}")
                        break

    except Exception as e:
        print(f"测试替代选择器失败: {e}")

if __name__ == "__main__":
    analyze_page_structure()
    test_alternative_selectors()
