# SlimCheck API Server - Dockerfile
# 使用 Python 3.11 官方镜像（LangGraph 兼容稳定）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/

# 创建数据目录（用于挂载 volume）
RUN mkdir -p /app/data/users /app/data/logs

# 设置非 root 用户（安全最佳实践）
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=40s \
    --retries=3 \
    CMD curl -f http://localhost:8083/api/v1/health || exit 1

# 暴露端口
EXPOSE 8083

# 启动命令
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8083", "--workers", "2"]
