#!/usr/bin/env bash
# ========================================
# SlimCheck API Server 启动脚本
# ========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting SlimCheck API Server..."

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，复制 .env.example..."
    cp .env.example .env
    echo "   请编辑 .env 文件配置你的 API Key"
fi

# 检查并创建数据目录
mkdir -p data/users data/logs

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 使用环境变量中的配置，默认值设置
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8083}
WORKERS=${WORKERS:-2}
# uvicorn 需要小写日志级别
LOG_LEVEL=$(echo ${LOG_LEVEL:-info} | tr '[:upper:]' '[:lower:]')

echo "📋 API Docs: http://${HOST}:${PORT}/docs"
echo "🔧 Workers: ${WORKERS}"
echo "🔴 Press Ctrl+C to stop server"
echo ""

exec python3 -m uvicorn src.server:app \
    --host ${HOST} \
    --port ${PORT} \
    --workers ${WORKERS} \
    --log-level ${LOG_LEVEL}
