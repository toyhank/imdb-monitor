# IMDB Top 250 监控程序 Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY *.py ./
COPY web/ ./web/
COPY api/ ./api/
COPY deploy/ ./deploy/
COPY config.env.example ./config.env

# 创建数据目录和日志目录
RUN mkdir -p /app/data /app/logs /app/backups

# 设置目录权限
RUN chmod 755 /app/data /app/logs /app/backups

# 创建非root用户
RUN useradd -m -u 1000 imdb && \
    chown -R imdb:imdb /app

USER imdb

# 暴露端口 (Web界面)
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30m --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://www.imdb.com', timeout=10)" || exit 1

# 设置数据卷
VOLUME ["/app/data", "/app/logs", "/app/backups"]

# 默认命令 (可通过环境变量覆盖)
CMD ["python", "main.py"]
