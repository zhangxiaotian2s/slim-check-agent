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

# 启动开发服务器
echo "📋 API Docs: http://localhost:8083/docs"
echo "🔴 Press Ctrl+C to stop server"
echo ""

exec python3 -m uvicorn src.server:app \
    --host 0.0.0.0 \
    --port 8083 \
    --reload \
    --log-level info
