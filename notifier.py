"""
通知发送模块
"""
import json
import smtplib
import logging
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional, List
from config import Config

logger = logging.getLogger(__name__)

class Notifier:
    """通知发送器"""
    
    def __init__(self):
        self.config = Config
        self.image_fetcher = None
    
    def send_notification(self, notification_data: Dict) -> bool:
        """发送通知"""
        if not notification_data['details']:
            logger.info("没有变化，跳过通知发送")
            return True
        
        success = True
        
        # 支持以逗号分隔的多种通知方式，如 "webhook,wechat_clawbot"
        notification_types = [t.strip() for t in self.config.NOTIFICATION_TYPE.split(',')]
        
        if 'webhook' in notification_types or 'both' in self.config.NOTIFICATION_TYPE:
            success &= self._send_webhook(notification_data)

        if 'email' in notification_types or 'both' in self.config.NOTIFICATION_TYPE:
            success &= self._send_email(notification_data)

        if 'wechat_clawbot' in notification_types:
            success &= self._send_wechat_clawbot(notification_data)

        return success

    def _send_wechat_clawbot(self, data: Dict) -> bool:
        """发送微信ClawBot通知"""
        if not self.config.WECHAT_CLAWBOT_PUSH_URL:
            logger.error("WeChat ClawBot 推送 URL 未配置")
            return False

        try:
            # 使用纯文本邮件格式作为微信推送消息内容，更加详细直观
            text_content = self._create_email_text(data)
            
            response = requests.post(
                self.config.WECHAT_CLAWBOT_PUSH_URL,
                json={"text": text_content},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                logger.info("微信ClawBot通知发送成功")
                return True
            else:
                logger.error(f"微信ClawBot通知发送失败: {result.get('error')}")
                return False
        except Exception as e:
            logger.error(f"微信ClawBot通知发送异常: {e}")
            return False

    def _get_image_fetcher(self):
        """延迟加载图片获取器"""
        if self.image_fetcher is None:
            try:
                from movie_images import MovieImageFetcher
                self.image_fetcher = MovieImageFetcher()
            except ImportError as e:
                logger.warning(f"无法导入图片模块: {e}")
                self.image_fetcher = False
        return self.image_fetcher if self.image_fetcher is not False else None

    def _get_movie_images_from_db(self, movies: list) -> dict:
        """从数据库获取电影图片信息"""
        movie_images = {}

        try:
            from database import DatabaseManager
            db = DatabaseManager()

            for movie in movies:
                imdb_id = movie.get('imdb_id')
                if not imdb_id:
                    continue

                # 从数据库获取电影信息
                import sqlite3
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT poster_path, title, chinese_title
                    FROM movies
                    WHERE imdb_id = ?
                """, (imdb_id,))

                result = cursor.fetchone()
                if result:
                    poster_path, title, chinese_title = result
                    if poster_path:
                        # 构建完整的TMDB图片URL
                        full_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                        movie_images[imdb_id] = {
                            'url': full_url,
                            'title': chinese_title or title,
                            'poster_path': poster_path
                        }
                        logger.debug(f"从数据库获取图片: {title} -> {full_url}")

                conn.close()

        except Exception as e:
            logger.error(f"从数据库获取图片失败: {e}")

        return movie_images
    
    def _send_webhook(self, data: Dict) -> bool:
        """发送Webhook通知"""
        if not self.config.WEBHOOK_URL:
            logger.error("Webhook URL未配置")
            return False

        try:
            # 根据webhook类型格式化数据
            webhook_type = getattr(self.config, 'WEBHOOK_TYPE', 'wework').lower()

            if webhook_type == 'wework':
                # 企业微信支持多种消息类型，先尝试发送图文消息
                payloads = self._format_wework_messages(data)
                return self._send_wework_messages(payloads)
            elif webhook_type == 'slack':
                payload = self._format_slack_message(data)
            else:
                # 通用格式
                payload = self._format_generic_message(data)

            # 发送POST请求
            response = requests.post(
                self.config.WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            response.raise_for_status()
            logger.info(f"Webhook通知发送成功 (类型: {webhook_type})")
            return True

        except requests.RequestException as e:
            logger.error(f"Webhook发送失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Webhook发送异常: {e}")
            return False

    def _send_wework_messages(self, payloads: List[Dict]) -> bool:
        """发送企业微信多条消息"""
        if not payloads:
            return False

        success_count = 0
        for i, payload in enumerate(payloads):
            try:
                response = requests.post(
                    self.config.WEBHOOK_URL,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()

                if result.get('errcode') == 0:
                    success_count += 1
                    logger.debug(f"企业微信消息 {i+1} 发送成功")
                else:
                    logger.error(f"企业微信消息 {i+1} 发送失败: {result}")

                # 避免发送过快
                if i < len(payloads) - 1:
                    import time
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"企业微信消息 {i+1} 发送异常: {e}")

        if success_count > 0:
            logger.info(f"企业微信通知发送完成: {success_count}/{len(payloads)} 成功")
            return True
        else:
            logger.error("所有企业微信消息发送失败")
            return False

    def _format_wework_messages(self, data: Dict) -> List[Dict]:
        """格式化企业微信消息（支持图文卡片）"""
        messages = []
        details = data['details']

        # 检查是否有新增或下架的电影
        has_new_or_removed = (details.get('new_entries') or details.get('removed_entries'))

        if has_new_or_removed and self.config.ENABLE_MOVIE_IMAGES:
            # 有新增或下架电影时，获取相关图片并创建图文消息
            movie_images = {}

            # 优先从数据库获取图片
            movies_for_images = []
            if details.get('new_entries'):
                movies_for_images.extend(details['new_entries'][:3])  # 最多3部新增电影
            if details.get('removed_entries'):
                movies_for_images.extend(details['removed_entries'][:2])  # 最多2部退出电影

            if movies_for_images:
                # 首先尝试从数据库获取图片
                movie_images = self._get_movie_images_from_db(movies_for_images)

                # 如果数据库中没有足够的图片，再尝试爬取
                if len(movie_images) < len(movies_for_images):
                    image_fetcher = self._get_image_fetcher()
                    if image_fetcher:
                        missing_movies = [m for m in movies_for_images if m.get('imdb_id') not in movie_images]
                        if missing_movies:
                            fetched_images = image_fetcher.get_multiple_posters(missing_movies, max_count=3)
                            movie_images.update(fetched_images)

            # 创建Markdown v2图文消息
            if movie_images or has_new_or_removed:  # 即使没有图片，有新增/下架也发图文消息
                markdown_v2_message = self._create_markdown_v2_message_for_new_removed(data, movie_images)
                messages.append(markdown_v2_message)
            else:
                # 回退到普通消息
                text_message = self._format_wework_message(data)
                messages.append(text_message)
        else:
            # 只有排名变化时使用Markdown v2消息
            markdown_message = self._create_markdown_v2_message_for_rank_changes(data)
            messages.append(markdown_message)

        return messages

    def _create_markdown_v2_message_for_new_removed(self, data: Dict, movie_images: Dict) -> Dict:
        """为新增/下架电影创建Markdown v2格式消息"""
        details = data['details']

        # 构建Markdown内容
        content = f"# 🎬 IMDB Top 250 榜单更新\n\n"
        content += f"**时间**: {details['timestamp'][:19]}\n"
        content += f"**摘要**: {details['summary']}\n\n"

        # 新增电影部分
        if details.get('new_entries'):
            content += "## 🆕 新进榜单\n\n"
            for entry in details['new_entries'][:3]:  # 最多显示3部
                imdb_id = entry.get('imdb_id')
                image_data = movie_images.get(imdb_id) if movie_images else None

                # 优先使用中文标题
                display_title = entry.get('display_title') or entry.get('chinese_title') or entry['title']

                content += f"### {display_title}\n"

                # 添加图片
                if image_data and image_data.get('url'):
                    content += f"![{display_title}]({image_data['url']})\n\n"

                content += f"- **排名**: #{entry['rank']}\n"
                content += f"- **年份**: {entry.get('year', '未知')}\n"
                content += f"- **评分**: {entry.get('rating', '未知')}\n"

                if imdb_id:
                    content += f"- **链接**: [查看详情](https://www.imdb.com/title/{imdb_id}/)\n"

                content += "\n"

        # 退出电影部分
        if details.get('removed_entries'):
            content += "## 📤 离开榜单\n\n"
            for entry in details['removed_entries'][:2]:  # 最多显示2部
                imdb_id = entry.get('imdb_id')
                image_data = movie_images.get(imdb_id) if movie_images else None

                # 优先使用中文标题
                display_title = entry.get('display_title') or entry.get('chinese_title') or entry['title']

                content += f"### {display_title}\n"

                # 添加图片
                if image_data and image_data.get('url'):
                    content += f"![{display_title}]({image_data['url']})\n\n"

                content += f"- **原排名**: #{entry['old_rank']}\n"
                content += f"- **年份**: {entry.get('year', '未知')}\n"

                if imdb_id:
                    content += f"- **链接**: [查看详情](https://www.imdb.com/title/{imdb_id}/)\n"

                content += "\n"

        # 添加底部链接
        content += "---\n"
        content += "[📊 查看完整榜单](https://www.imdb.com/chart/top/)"

        return {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

    def _create_markdown_v2_message_for_rank_changes(self, data: Dict) -> Dict:
        """为排名变化创建Markdown v2格式消息"""
        details = data['details']

        # 构建Markdown内容
        content = f"# 🎬 IMDB Top 250 排名变化\n\n"
        content += f"**时间**: {details['timestamp'][:19]}\n"
        content += f"**摘要**: {details['summary']}\n\n"

        # 排名变化部分
        if details.get('rank_changes'):
            content += "## 📊 排名变化\n\n"

            # 按变化幅度排序，显示最大的变化
            rank_changes = sorted(details['rank_changes'],
                                key=lambda x: abs(x.get('change', 0)) if isinstance(x.get('change'), (int, float)) else 0, reverse=True)

            for change in rank_changes[:10]:  # 最多显示10个变化
                display_title = change.get('display_title') or change.get('chinese_title') or change['title']
                old_rank = change['old_rank']
                new_rank = change['new_rank']
                change_value = change.get('change', 0)

                # 确定变化方向的emoji
                if change_value > 0:
                    direction = "📈"
                    change_text = f"+{change_value}"
                elif change_value < 0:
                    direction = "📉"
                    change_text = str(change_value)
                else:
                    direction = "➡️"
                    change_text = "0"

                content += f"### {direction} {display_title}\n"
                content += f"- **排名变化**: #{old_rank} → #{new_rank} ({change_text})\n"
                content += f"- **年份**: {change.get('year', '未知')}\n"

                imdb_id = change.get('imdb_id')
                if imdb_id:
                    content += f"- **链接**: [查看详情](https://www.imdb.com/title/{imdb_id}/)\n"

                content += "\n"

            # 如果有更多变化，显示统计
            if len(details['rank_changes']) > 10:
                remaining = len(details['rank_changes']) - 10
                content += f"*还有 {remaining} 部电影排名发生变化...*\n\n"

        # 添加底部链接
        content += "---\n"
        content += "[📊 查看完整榜单](https://www.imdb.com/chart/top/)"

        return {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

    def _create_news_message_for_new_removed(self, data: Dict, movie_images: Dict) -> Dict:
        """为新增/下架电影创建图文消息"""
        details = data['details']
        articles = []

        # 主要文章 - 包含总体摘要
        main_title = "🎬 IMDB Top 250 榜单更新"
        main_description = f"时间: {details['timestamp'][:19]}\n{details['summary']}"

        main_article = {
            "title": main_title,
            "description": main_description,
            "url": "https://www.imdb.com/chart/top/",
            "picurl": ""
        }

        # 如果有新增电影的图片，使用第一张作为主图
        if movie_images and details.get('new_entries'):
            first_new_movie = details['new_entries'][0]
            first_image = movie_images.get(first_new_movie.get('imdb_id'))
            if first_image:
                main_article["picurl"] = first_image.get('url', '')

        articles.append(main_article)

        # 为新增电影创建子文章
        if details.get('new_entries'):
            for entry in details['new_entries'][:3]:  # 最多显示3部
                imdb_id = entry.get('imdb_id')
                image_data = movie_images.get(imdb_id) if movie_images else None

                # 优先使用中文标题
                display_title = entry.get('display_title') or entry.get('chinese_title') or entry['title']

                article = {
                    "title": f"🆕 {display_title}",
                    "description": f"新进榜单 #{entry['rank']}\n年份: {entry.get('year', '未知')}\n评分: {entry.get('rating', '未知')}",
                    "url": f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else "https://www.imdb.com/chart/top/",
                    "picurl": image_data.get('url', '') if image_data else ''
                }
                articles.append(article)

        # 为下架电影创建子文章（现在也支持图片）
        if details.get('removed_entries'):
            for entry in details['removed_entries'][:2]:  # 最多显示2部，为新增电影留空间
                imdb_id = entry.get('imdb_id')
                image_data = movie_images.get(imdb_id) if movie_images else None

                # 优先使用中文标题
                display_title = entry.get('display_title') or entry.get('chinese_title') or entry['title']

                article = {
                    "title": f"📤 {display_title}",
                    "description": f"离开榜单\n原排名: #{entry['old_rank']}\n年份: {entry.get('year', '未知')}",
                    "url": f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else "https://www.imdb.com/chart/top/",
                    "picurl": image_data.get('url', '') if image_data else ''
                }
                articles.append(article)

        return {
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }

    def _create_news_message(self, data: Dict, movie_images: Dict) -> Dict:
        """创建企业微信图文消息"""
        details = data['details']
        articles = []

        # 主要文章 - 包含总体摘要
        main_article = {
            "title": "🎬 IMDB Top 250 变化通知",
            "description": f"时间: {details['timestamp'][:19]}\n{details['summary']}",
            "url": "https://www.imdb.com/chart/top/",
            "picurl": ""
        }

        # 如果有图片，使用第一张作为主图
        if movie_images:
            first_image = list(movie_images.values())[0]
            # 企业微信图文消息需要图片URL，不能直接使用base64
            # 这里我们使用原始URL（如果可用）
            main_article["picurl"] = first_image.get('url', '')

        articles.append(main_article)

        # 为每个有图片的电影创建子文章
        for imdb_id, image_data in list(movie_images.items())[:3]:  # 最多3个
            # 找到对应的电影信息
            movie_info = None
            for change in details.get('rank_changes', []):
                if change.get('imdb_id') == imdb_id:
                    movie_info = change
                    break

            if movie_info:
                direction = "📈" if "↑" in movie_info.get('change', '') else "📉"
                display_title = movie_info.get('display_title') or movie_info.get('chinese_title') or movie_info['title']
                article = {
                    "title": f"{direction} {display_title}",
                    "description": f"排名变化: #{movie_info['old_rank']} → #{movie_info['new_rank']} ({movie_info.get('change', '')})",
                    "url": f"https://www.imdb.com/title/{imdb_id}/",
                    "picurl": image_data.get('url', '')
                }
                articles.append(article)

        return {
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }

    def _format_wework_message(self, data: Dict) -> Dict:
        """格式化企业微信机器人消息"""
        details = data['details']

        # 构建Markdown格式的消息
        content = f"# 🎬 IMDB Top 250 变化通知\n\n"
        content += f"**时间**: {details['timestamp'][:19]}\n"
        content += f"**摘要**: {details['summary']}\n\n"

        # 排名变化
        if 'rank_changes' in details and details['rank_changes']:
            content += "## 📊 排名变化\n"
            for change in details['rank_changes'][:5]:  # 只显示前5个
                direction = "🔺" if "↑" in change['change'] else "🔻"
                display_title = change.get('display_title') or change.get('chinese_title') or change['title']
                content += f"- {direction} **{display_title}**: #{change['old_rank']} → #{change['new_rank']} ({change['change']})\n"

            if len(details['rank_changes']) > 5:
                content += f"- ... 还有 {len(details['rank_changes']) - 5} 部电影排名发生变化\n"
            content += "\n"

        # 新增电影
        if 'new_entries' in details and details['new_entries']:
            content += "## 🆕 新进榜单\n"
            for entry in details['new_entries'][:3]:  # 只显示前3个
                display_title = entry.get('display_title') or entry.get('chinese_title') or entry['title']
                content += f"- ⭐ **{display_title}**: #{entry['rank']}\n"

            if len(details['new_entries']) > 3:
                content += f"- ... 还有 {len(details['new_entries']) - 3} 部新电影\n"
            content += "\n"

        # 移除的电影
        if 'removed_entries' in details and details['removed_entries']:
            content += "## 📤 离开榜单\n"
            for entry in details['removed_entries'][:3]:  # 只显示前3个
                display_title = entry.get('display_title') or entry.get('chinese_title') or entry['title']
                content += f"- 👋 **{display_title}**: 原#{entry['old_rank']}\n"

            if len(details['removed_entries']) > 3:
                content += f"- ... 还有 {len(details['removed_entries']) - 3} 部电影离开\n"
            content += "\n"

        content += "---\n*IMDB Top 250 监控系统*"

        return {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

    def _format_slack_message(self, data: Dict) -> Dict:
        """格式化Slack消息"""
        details = data['details']

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎬 IMDB Top 250 变化通知"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*时间:*\n{details['timestamp'][:19]}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*摘要:*\n{details['summary']}"
                    }
                ]
            }
        ]

        # 添加变化详情
        if 'rank_changes' in details and details['rank_changes']:
            rank_text = ""
            for change in details['rank_changes'][:5]:
                direction = ":arrow_up:" if "↑" in change['change'] else ":arrow_down:"
                rank_text += f"{direction} *{change['title']}*: #{change['old_rank']} → #{change['new_rank']}\n"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📊 排名变化:*\n{rank_text}"
                }
            })

        return {
            "blocks": blocks
        }

    def _format_generic_message(self, data: Dict) -> Dict:
        """格式化通用消息"""
        return {
            'text': data['message'],
            'timestamp': data['details']['timestamp'],
            'summary': data['details']['summary'],
            'changes': data['details']
        }

    def _send_email(self, data: Dict) -> bool:
        """发送邮件通知"""
        if not all([self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD, self.config.EMAIL_TO]):
            logger.error("邮件配置不完整")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"IMDB Top 250 变化通知 - {data['details']['timestamp'][:10]}"
            msg['From'] = self.config.EMAIL_USERNAME
            msg['To'] = self.config.EMAIL_TO
            
            # 创建HTML内容
            html_content = self._create_email_html(data)
            
            # 创建纯文本内容
            text_content = self._create_email_text(data)
            
            # 添加内容
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # 发送邮件
            with smtplib.SMTP(self.config.EMAIL_SMTP_SERVER, self.config.EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USERNAME, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info("邮件通知发送成功")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def _create_email_html(self, data: Dict) -> str:
        """创建HTML邮件内容"""
        details = data['details']
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .movie {{ margin: 10px 0; padding: 10px; border-left: 3px solid #007cba; }}
                .rank-up {{ color: #28a745; }}
                .rank-down {{ color: #dc3545; }}
                .new-entry {{ color: #007cba; }}
                .removed {{ color: #6c757d; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>IMDB Top 250 变化通知</h2>
                <p><strong>时间:</strong> {details['timestamp']}</p>
                <p><strong>摘要:</strong> {details['summary']}</p>
            </div>
        """
        
        # 排名变化
        if 'rank_changes' in details:
            html += """
            <div class="section">
                <h3>排名变化</h3>
                <table>
                    <tr>
                        <th>电影</th>
                        <th>年份</th>
                        <th>评分</th>
                        <th>原排名</th>
                        <th>新排名</th>
                        <th>变化</th>
                    </tr>
            """
            for change in details['rank_changes']:
                change_class = 'rank-up' if '↑' in change['change'] else 'rank-down'
                html += f"""
                    <tr>
                        <td>{change['title']}</td>
                        <td>{change.get('year', 'N/A')}</td>
                        <td>{change.get('rating', 'N/A')}</td>
                        <td>#{change['old_rank']}</td>
                        <td>#{change['new_rank']}</td>
                        <td class="{change_class}">{change['change']}</td>
                    </tr>
                """
            html += "</table></div>"
        
        # 新增电影
        if 'new_entries' in details:
            html += """
            <div class="section">
                <h3>新进榜单</h3>
                <table>
                    <tr>
                        <th>电影</th>
                        <th>年份</th>
                        <th>评分</th>
                        <th>排名</th>
                    </tr>
            """
            for entry in details['new_entries']:
                html += f"""
                    <tr>
                        <td class="new-entry">{entry['title']}</td>
                        <td>{entry.get('year', 'N/A')}</td>
                        <td>{entry.get('rating', 'N/A')}</td>
                        <td>#{entry['rank']}</td>
                    </tr>
                """
            html += "</table></div>"
        
        # 移除的电影
        if 'removed_entries' in details:
            html += """
            <div class="section">
                <h3>离开榜单</h3>
                <table>
                    <tr>
                        <th>电影</th>
                        <th>年份</th>
                        <th>评分</th>
                        <th>原排名</th>
                    </tr>
            """
            for entry in details['removed_entries']:
                html += f"""
                    <tr>
                        <td class="removed">{entry['title']}</td>
                        <td>{entry.get('year', 'N/A')}</td>
                        <td>{entry.get('rating', 'N/A')}</td>
                        <td>#{entry['old_rank']}</td>
                    </tr>
                """
            html += "</table></div>"
        
        html += "</body></html>"
        return html
    
    def _create_email_text(self, data: Dict) -> str:
        """创建纯文本邮件内容"""
        details = data['details']
        text = f"""IMDB Top 250 变化通知

时间: {details['timestamp']}
摘要: {details['summary']}

"""
        
        # 排名变化
        if 'rank_changes' in details:
            text += "排名变化:\n"
            for change in details['rank_changes']:
                text += f"  • {change['title']} ({change.get('year', 'N/A')}) - #{change['old_rank']} → #{change['new_rank']} ({change['change']})\n"
            text += "\n"
        
        # 新增电影
        if 'new_entries' in details:
            text += "新进榜单:\n"
            for entry in details['new_entries']:
                text += f"  • {entry['title']} ({entry.get('year', 'N/A')}) - #{entry['rank']}\n"
            text += "\n"
        
        # 移除的电影
        if 'removed_entries' in details:
            text += "离开榜单:\n"
            for entry in details['removed_entries']:
                text += f"  • {entry['title']} ({entry.get('year', 'N/A')}) - 原#{entry['old_rank']}\n"
            text += "\n"
        
        return text
