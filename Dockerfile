# ============================================================
# Telegram MCP Complete - Dockerfile
# ============================================================
# 用于构建 Docker 镜像，支持 Dashboard 和 MCP 服务器

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目代码
COPY *.py ./
COPY static ./static/
COPY .env.example .env

# 创建数据目录
RUN mkdir -p /app/accounts

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/accounts').read()" || exit 1

# 启动 Dashboard
CMD ["python3", "dashboard.py"]
