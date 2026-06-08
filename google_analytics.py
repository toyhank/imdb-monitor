"""
Google Analytics 集成模块
简化版本，只支持Google Analytics统计
"""
import logging
from config import Config

logger = logging.getLogger(__name__)


class GoogleAnalytics:
    """Google Analytics管理器"""
    
    def __init__(self):
        self.tracking_id = Config.GOOGLE_ANALYTICS_ID
        self.enabled = Config.ENABLE_ANALYTICS and bool(self.tracking_id)
        
        if self.enabled:
            logger.info(f"Google Analytics已启用，跟踪ID: {self.tracking_id}")
        else:
            logger.info("Google Analytics未启用")
    
    def is_enabled(self) -> bool:
        """检查是否启用Google Analytics"""
        return self.enabled
    
    def get_tracking_script(self) -> str:
        """生成Google Analytics跟踪脚本"""
        if not self.enabled:
            return ""
        
        return f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={self.tracking_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  
  gtag('config', '{self.tracking_id}', {{
    'anonymize_ip': true,
    'allow_google_signals': false,
    'allow_ad_personalization_signals': false
  }});
  
  // 自定义事件跟踪
  document.addEventListener('DOMContentLoaded', function() {{
    // 跟踪外部链接点击
    document.addEventListener('click', function(e) {{
      var link = e.target.closest('a');
      if (link && link.hostname !== window.location.hostname) {{
        gtag('event', 'click', {{
          'event_category': 'external_link',
          'event_label': link.href,
          'transport_type': 'beacon'
        }});
      }}
    }});
    
    // 跟踪文件下载
    document.addEventListener('click', function(e) {{
      var link = e.target.closest('a');
      if (link && link.href.match(/\\.(pdf|doc|docx|xls|xlsx|zip|rar|exe|dmg)$/i)) {{
        gtag('event', 'download', {{
          'event_category': 'file_download',
          'event_label': link.href,
          'transport_type': 'beacon'
        }});
      }}
    }});
    
    // 跟踪Excel导出
    document.addEventListener('click', function(e) {{
      if (e.target.closest('.export-btn') || e.target.closest('[data-action="export"]')) {{
        gtag('event', 'export', {{
          'event_category': 'data_export',
          'event_label': 'excel_export',
          'transport_type': 'beacon'
        }});
      }}
    }});
    
    // 跟踪搜索
    var searchInput = document.querySelector('#search-input');
    if (searchInput) {{
      var searchTimeout;
      searchInput.addEventListener('input', function() {{
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {{
          if (searchInput.value.length > 2) {{
            gtag('event', 'search', {{
              'event_category': 'site_search',
              'event_label': searchInput.value,
              'transport_type': 'beacon'
            }});
          }}
        }}, 1000);
      }});
    }}
    
    // 跟踪页面滚动深度
    var scrollDepth = 0;
    var maxScroll = 0;
    window.addEventListener('scroll', function() {{
      var scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
      if (scrollPercent > maxScroll && scrollPercent % 25 === 0) {{
        maxScroll = scrollPercent;
        gtag('event', 'scroll', {{
          'event_category': 'engagement',
          'event_label': scrollPercent + '%',
          'value': scrollPercent,
          'transport_type': 'beacon'
        }});
      }}
    }});
    
    // 跟踪页面停留时间
    var startTime = Date.now();
    window.addEventListener('beforeunload', function() {{
      var timeSpent = Math.round((Date.now() - startTime) / 1000);
      if (timeSpent > 10) {{ // 只跟踪停留超过10秒的访问
        gtag('event', 'timing_complete', {{
          'event_category': 'engagement',
          'event_label': 'time_on_page',
          'value': timeSpent,
          'transport_type': 'beacon'
        }});
      }}
    }});
  }});
</script>"""
    
    def get_noscript_tag(self) -> str:
        """生成noscript标签（用于无JavaScript环境）"""
        if not self.enabled:
            return ""
        
        return f"""
<!-- Google Analytics (noscript) -->
<noscript>
  <img src="https://www.googletagmanager.com/ns.html?id={self.tracking_id}" 
       style="display:none;visibility:hidden" alt="">
</noscript>"""
    
    def track_server_event(self, event_name: str, parameters: dict = None):
        """
        服务器端事件跟踪（需要Measurement Protocol）
        注意：这需要额外的配置和API密钥
        """
        if not self.enabled:
            return
        
        # 这里可以实现服务器端事件跟踪
        # 需要使用Google Analytics Measurement Protocol
        logger.info(f"服务器事件: {event_name}, 参数: {parameters}")
    
    def get_config_status(self) -> dict:
        """获取配置状态"""
        return {
            'enabled': self.enabled,
            'tracking_id': self.tracking_id if self.enabled else None,
            'features': {
                'anonymize_ip': True,
                'external_link_tracking': True,
                'download_tracking': True,
                'search_tracking': True,
                'scroll_tracking': True,
                'timing_tracking': True
            }
        }


# 创建全局实例
google_analytics = GoogleAnalytics()
