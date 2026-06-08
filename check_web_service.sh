#!/bin/bash

# IMDB监控系统 Web服务检查脚本
# 检查Web服务是否正常运行，如果不运行则自动重启

# 配置
WEB_PORT=${WEB_PORT:-5000}
MAX_RETRIES=3
RETRY_INTERVAL=10

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"; }
log_warn() { echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"; }
log_error() { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"; }

# 检查Web服务是否运行
check_web_service() {
    # 方法1: 检查端口
    if netstat -tlnp 2>/dev/null | grep -q ":$WEB_PORT "; then
        return 0
    fi
    
    # 方法2: 检查进程
    if pgrep -f "python.*main.py.*--web" >/dev/null; then
        return 0
    fi
    
    return 1
}

# 检查Web服务响应
check_web_response() {
    if curl -s --connect-timeout 5 "http://localhost:$WEB_PORT" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# 启动Web服务
start_web_service() {
    log_info "尝试启动Web服务..."
    
    # 尝试systemd
    if systemctl list-unit-files | grep -q "imdb-monitor-web.service"; then
        sudo systemctl start imdb-monitor-web
        sleep 5
        if check_web_service; then
            log_info "systemd服务启动成功"
            return 0
        fi
    fi
    
    # 尝试supervisor
    if command -v supervisorctl >/dev/null && sudo supervisorctl status imdb-monitor-web >/dev/null 2>&1; then
        sudo supervisorctl start imdb-monitor-web
        sleep 5
        if check_web_service; then
            log_info "supervisor服务启动成功"
            return 0
        fi
    fi
    
    # 尝试PM2
    if command -v pm2 >/dev/null && pm2 list | grep -q imdb-monitor-web; then
        pm2 start imdb-monitor-web
        sleep 5
        if check_web_service; then
            log_info "PM2服务启动成功"
            return 0
        fi
    fi
    
    # 尝试screen
    if [[ -f manage_web_screen.sh ]]; then
        ./manage_web_screen.sh start
        sleep 5
        if check_web_service; then
            log_info "screen会话启动成功"
            return 0
        fi
    fi
    
    # 最后尝试直接启动
    log_warn "尝试直接启动Web服务..."
    cd "$(dirname "$0")"
    
    if [[ -d venv ]]; then
        source venv/bin/activate
        nohup python main.py --web > logs/web_auto.log 2>&1 &
    else
        nohup python3 main.py --web > logs/web_auto.log 2>&1 &
    fi
    
    sleep 5
    if check_web_service; then
        log_info "直接启动成功"
        return 0
    fi
    
    log_error "所有启动方法都失败了"
    return 1
}

# 主检查逻辑
main() {
    log_info "开始检查Web服务状态..."
    
    # 检查服务是否运行
    if check_web_service; then
        log_info "Web服务正在运行"
        
        # 检查服务是否响应
        if check_web_response; then
            log_info "Web服务响应正常"
            exit 0
        else
            log_warn "Web服务无响应，尝试重启..."
        fi
    else
        log_warn "Web服务未运行，尝试启动..."
    fi
    
    # 尝试重启服务
    for i in $(seq 1 $MAX_RETRIES); do
        log_info "第 $i 次尝试启动服务..."
        
        # 先停止可能存在的僵尸进程
        pkill -f "python.*main.py.*--web" 2>/dev/null || true
        sleep 2
        
        # 启动服务
        if start_web_service; then
            # 等待服务完全启动
            sleep 10
            
            # 验证服务
            if check_web_service && check_web_response; then
                log_info "Web服务启动成功并响应正常"
                exit 0
            else
                log_warn "服务启动但响应异常"
            fi
        fi
        
        if [[ $i -lt $MAX_RETRIES ]]; then
            log_warn "等待 $RETRY_INTERVAL 秒后重试..."
            sleep $RETRY_INTERVAL
        fi
    done
    
    log_error "Web服务启动失败，已尝试 $MAX_RETRIES 次"
    
    # 发送通知（如果配置了的话）
    if [[ -f config.env ]]; then
        source config.env
        if [[ -n "$WEBHOOK_URL" ]]; then
            curl -s -X POST "$WEBHOOK_URL" \
                -H 'Content-Type: application/json' \
                -d '{
                    "msgtype": "text",
                    "text": {
                        "content": "⚠️ IMDB监控系统Web服务启动失败，请检查服务器状态"
                    }
                }' >/dev/null 2>&1 || true
        fi
    fi
    
    exit 1
}

# 如果作为cron任务运行，添加日志
if [[ "${1:-}" == "--cron" ]]; then
    # 重定向输出到日志文件
    mkdir -p logs
    exec >> logs/web_check.log 2>&1
fi

main "$@"
