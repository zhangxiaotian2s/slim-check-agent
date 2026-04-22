# SlimCheck API Server

基于 FastAPI + LangGraph 的卡路里管理多智能体系统服务端。

## ✨ 功能特性

- **流式输出**: SSE 实时返回分析进度和中间结果
- **并行请求**: 支持多个请求同时处理，带并发控制
- **请求追踪**: 前端携带 UUID，全链路可追踪
- **可取消**: 支持中途取消请求，节约 LLM 资源
- **健康检查**: Kubernetes 友好的 liveness/readiness 探针
- **Docker 部署**: 一键容器化部署
- **完整 API**: 用户注册/查询、流式分析、请求管理

## 🚀 快速开始

### 方式一：本地启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY 等信息

# 3. 启动服务
./start.sh
# 或直接运行: uvicorn src.server:app --reload
```

### 方式二：Docker Compose

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f slimcheck-api

# 4. 停止服务
docker-compose down
```

## 📚 API 文档

启动服务后访问：

- **Swagger UI**: http://localhost:8083/docs
- **ReDoc**: http://localhost:8083/redoc
- **OpenAPI JSON**: http://localhost:8083/openapi.json

## 🔌 核心接口

### 1. 流式分析接口

```http
POST /api/v1/analyze/stream
Content-Type: application/json
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000

{
  "input_type": "text_only",
  "text": "早餐吃了一个包子，喝了一杯豆浆，然后慢跑30分钟",
  "person_id": "0a5f4a0c"
}
```

**SSE 事件类型**:

| 事件 | 说明 |
|------|------|
| `status` | 阶段更新，包含进度(0-100) |
| `partial_result` | 中间结果（饮食/运动/健康点评） |
| `error` | 错误信息 |
| `complete` | 分析完成 |
| `cancelled` | 请求被取消 |

**前端示例代码**:

```javascript
const eventSource = new EventSource('/api/v1/analyze/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Request-ID': crypto.randomUUID()
  },
  body: JSON.stringify({
    input_type: 'text_only',
    text: '早餐吃了一个包子，喝了一杯豆浆',
    person_id: '0a5f4a0c'
  })
});

eventSource.addEventListener('status', (e) => {
  const data = JSON.parse(e.data);
  console.log(`进度: ${data.progress}% - ${data.message}`);
});

eventSource.addEventListener('partial_result', (e) => {
  const data = JSON.parse(e.data);
  if (data.type === 'food_items') {
    console.log('饮食分析结果:', data.data);
  }
});

eventSource.addEventListener('complete', () => {
  eventSource.close();
});
```

### 2. 用户注册

```http
POST /api/v1/users/register
Content-Type: application/json

{
  "gender": "male",
  "age": 30,
  "height": 175,
  "weight": 75,
  "activity_level": "moderate",
  "name": "张三"
}
```

### 3. 请求管理

```http
# 查询请求状态
GET /api/v1/requests/{request_id}/status

# 取消请求
POST /api/v1/requests/{request_id}/cancel

# 列出所有请求
GET /api/v1/requests

# 获取统计信息
GET /api/v1/requests/stats
```

### 4. 健康检查

```http
GET /api/v1/health          # 基础健康检查
GET /api/v1/health/detailed  # 详细健康检查（含内存/CPU）
GET /api/v1/ready            # 就绪检查
```

## 🏗️ 项目结构

```
slim-check-agent/
├── src/
│   ├── server.py                    # FastAPI 服务入口
│   ├── main.py                      # CLI 入口（保留）
│   ├── agents/                      # 智能体实现
│   ├── graph/                       # LangGraph 工作流
│   ├── models/
│   │   ├── api_models.py           # ✅ API 请求/响应模型
│   │   └── ...
│   ├── api/                         # ✅ API 路由
│   │   ├── router_health.py        # 健康检查
│   │   ├── router_analyze.py       # 流式分析
│   │   ├── router_users.py         # 用户管理
│   │   └── router_requests.py      # 请求管理
│   └── utils/
│       ├── request_manager.py      # ✅ 请求管理器（并发控制）
│       ├── sse_utils.py            # ✅ SSE 事件工具
│       ├── logger.py               # 日志
│       └── ...
├── config/
│   ├── settings.py                  # ✅ Pydantic 配置
│   └── ...
├── Dockerfile                       # ✅ Docker 镜像
├── docker-compose.yml               # ✅ Docker Compose
├── requirements.txt                 # ✅ 更新的依赖
├── .env.example                     # ✅ 环境变量示例
├── start.sh                         # ✅ 启动脚本
└── README.md
```

## ⚙️ 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_BASE_URL` | - | LLM API 地址 |
| `OPENAI_API_KEY` | - | API Key |
| `OPENAI_MODEL` | `doubao-seed-2.0-pro` | 模型名称 |
| `MAX_CONCURRENT_REQUESTS` | `10` | 最大并发请求数 |
| `REQUEST_TIMEOUT_SECONDS` | `120` | 单请求超时时间 |
| `CORS_ORIGINS` | `*` | CORS 允许的来源 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DEBUG` | `false` | 调试模式 |

## 📊 并发控制机制

```
并发请求限制: 10（可配置）
         │
         ▼
  ┌─────────────┐
  │  请求队列   │ 等待中的请求
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ 执行中的请求 │ 最多 10 个并行
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ LLM 客户端池 │
  └─────────────┘
```

- 超过并发限制的请求进入等待队列
- 等待超时（30秒）返回 429 错误
- 请求可随时取消，立即释放槽位

## 🔍 监控与可观测性

### 请求追踪

每个请求都通过 `X-Request-ID` 头追踪：
- 所有日志都携带 request_id
- 所有 SSE 事件都携带 request_id
- 可随时查询请求状态和执行阶段

### 日志示例

```
[req:550e8400...] Processing node: analyze_diet
[req:550e8400...] Analysis completed in 12500ms
```

## 🐳 Docker 部署说明

### 构建镜像

```bash
docker build -t slimcheck-api .
```

### 运行容器

```bash
docker run -d \
  --name slimcheck-api \
  -p 8083:8083 \
  -v $(pwd)/data:/app/data \
  -e OPENAI_BASE_URL=https://... \
  -e OPENAI_API_KEY=your-key \
  slimcheck-api
```

### Docker Compose

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

## 🔒 生产环境建议

1. **启用认证**: 设置 `API_KEY_ENABLED=true` 并配置 `API_KEY`
2. **配置 CORS**: 设置 `CORS_ORIGINS` 为你的前端域名
3. **启用限流**: 设置 `RATE_LIMIT_ENABLED=true`
4. **使用 HTTPS**: 配置反向代理（Nginx/Caddy）提供 HTTPS
5. **监控告警**: 接入 Prometheus + Grafana 监控
6. **日志收集**: 结构化日志输出到 Loki/ELK

## 🧪 测试

```bash
# 健康检查
curl http://localhost:8083/api/v1/health

# 注册用户
curl -X POST http://localhost:8083/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"gender":"male","age":30,"height":175,"weight":75}'

# 流式分析（使用浏览器或 EventSource 客户端）
```

## 📝 开发说明

### 添加新的 API 路由

1. 在 `src/api/` 下创建新的 router 文件
2. 在 `src/server.py` 中注册路由
3. 在 `src/models/api_models.py` 中定义请求/响应模型

### 扩展 LangGraph 节点

1. 在 `src/graph/calorie_graph.py` 添加节点
2. 在 `src/utils/sse_utils.py` 的 `STAGE_MAPPING` 添加阶段显示
3. 在 `_extract_result_data` 添加结果提取逻辑（如果需要）

## 🤝 常见问题

**Q: 如何调整并发数？**

A: 设置环境变量 `MAX_CONCURRENT_REQUESTS=20`

**Q: 请求超时时间太短？**

A: 设置环境变量 `REQUEST_TIMEOUT_SECONDS=300`

**Q: 如何查看当前活跃请求？**

A: 调用 `GET /api/v1/requests/stats` 接口

**Q: 支持图片上传吗？**

A: 流式分析接口支持 base64 编码图片，后续将添加 multipart/form-data 文件上传支持
