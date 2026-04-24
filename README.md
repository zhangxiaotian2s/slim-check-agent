# SlimCheck-agent

基于 Python + LangGraph 开发的卡路里管理多智能体系统，支持 Web API 服务和命令行两种使用方式。

通过多个专业智能体分工协作，分析饮食和运动的卡路里，并结合个人身体信息给出健康建议和综合点评。

## ✨ 功能特点

### 输入方式
- ✅ **纯食物图片分析** - 上传食物图片，AI自动识别食物种类并估算份量
- ✅ **食物图片 + 文字描述** - 图片结合文字描述提高准确性
- ✅ **纯文字饮食分析** - 文字描述你吃了什么，直接计算卡路里
- ✅ **纯文字运动分析** - 文字描述你做了什么运动，计算消耗卡路里
- ✅ **同时包含饮食和运动** - 支持一句话同时描述饮食和运动，自动分别分析

### 部署方式
- ✅ **Web API 服务** - FastAPI 服务，支持 SSE 流式输出
- ✅ **前端界面** - Vue3 + TypeScript 单页应用
- ✅ **命令行工具** - CLI 命令行工具（保留传统方式）

### 多智能体架构

| 智能体 | 职责 |
|--------|------|
| **图片分析专家** | 从图片识别食物种类，估算每份重量(克) |
| **饮食分析专家** | 根据识别出的食物计算卡路里和营养素(蛋白质/碳水/脂肪) |
| **运动分析专家** | 根据运动描述计算卡路里消耗 |
| **个人健康管理专家** | 创建个人健康档案，计算BMI、基础代谢率、每日所需卡路里 |
| **健康综合点评专家** | 基于饮食/运动分析结果，提供专业健康点评和个性化建议 |

### 核心功能
- ✅ **流式输出** - SSE 实时返回分析进度和中间结果，类似 ChatGPT 打字机效果
- ✅ **实时进度** - 前端实时显示 AI 思考过程和分析进度
- ✅ **健康综合点评** - 基于AI的专业健康评估和个性化建议
- ✅ **多维度分析** - 同时支持饮食分析、运动分析或两者结合分析
- ✅ **并发控制** - 支持多请求并行处理，内置限流和超时机制
- ✅ **可取消请求** - 支持中途取消请求，节约 LLM 资源
- ✅ **请求追踪** - UUID 全链路追踪，可随时查询请求状态
- ✅ **用户档案管理** - 支持用户注册、查询、列表、删除
- ✅ **数据存储可扩展** - 支持 JSON 文件存储 和 MySQL 数据库存储
- ✅ **提示词独立维护** - 所有提示词都放在单独的 `src/prompts/` 目录，方便优化调整
- ✅ **清晰的日志系统** - 日志同时输出到控制台和 `data/logs/` 文件
- ✅ **健康检查** - Kubernetes 友好的 liveness/readiness 探针

---

## 🚀 快速开始

### 方式一：一键启动（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key 和数据库配置

# 2. 启动后端服务
./start.sh
```

服务启动后访问：
- **后端 API**: http://localhost:8083
- **API 文档**: http://localhost:8083/docs
- **前端界面**: cd frontend && npm install && npm run dev (http://localhost:5173)

### 直接使用 uvicorn 启动

```bash
# 生产环境（推荐，使用 2 个 workers）
python3 -m uvicorn src.server:app --host 0.0.0.0 --port 8083 --workers 2

# 开发环境（热重载）
python3 -m uvicorn src.server:app --host 0.0.0.0 --port 8083 --reload
```

---

## 🏗️ 技术架构

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| **前端** | Vue 3 + TypeScript + Vite |
| **后端框架** | FastAPI + Uvicorn |
| **多智能体** | LangGraph |
| **LLM 接口** | 兼容 OpenAI 格式（火山引擎豆包、OpenAI 等） |
| **数据存储** | MySQL / JSON 文件 |
| **流式输出** | SSE (Server-Sent Events) |
| **图片处理** | Pillow |
| **数据验证** | Pydantic v2 |
| **部署** | Uvicorn (支持多进程 workers) |

### 完整项目结构

```
.
├── .env                    # 环境配置（你的API信息）
├── .env.example            # 环境配置示例
├── .gitignore
├── requirements.txt        # Python 依赖
├── start.sh               # 后端启动脚本
├── README.md              # 本文档
├── API_SERVER.md          # API 服务详细文档
├── API_DOCUMENTATION.md   # 完整 API 接口文档
├── DESIGN.md              # 设计文档
├── config/
│   ├── __init__.py        # 配置单例
│   └── settings.py        # Pydantic 配置管理
├── src/
│   ├── __init__.py
│   ├── server.py          # ✅ FastAPI 服务入口
│   ├── main.py            # CLI 命令行入口（保留）
│   ├── agents/            # 智能体实现
│   │   ├── __init__.py
│   │   ├── base_agent.py               # 智能体基类
│   │   ├── image_analyst_agent.py     # 图片分析专家
│   │   ├── diet_analyst_agent.py      # 饮食分析专家
│   │   ├── exercise_analyst_agent.py  # 运动分析专家
│   │   ├── health_manager_agent.py   # 个人健康管理专家
│   │   └── health_review_agent.py    # 健康综合点评专家
│   ├── prompts/           # 独立提示词（方便维护）
│   │   ├── __init__.py
│   │   ├── image_analyst_prompt.py    # 图片分析提示词
│   │   ├── diet_analyst_prompt.py     # 饮食分析提示词
│   │   ├── exercise_analyst_prompt.py # 运动分析提示词
│   │   ├── health_manager_prompt.py  # 健康管理提示词
│   │   ├── health_review_prompt.py   # 健康综合点评提示词
│   │   └── router_prompt.py          # 输入分类提示词
│   ├── graph/             # LangGraph 工作流定义
│   │   ├── __init__.py
│   │   ├── state.py                # 状态定义
│   │   └── calorie_graph.py        # 流程图构建
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── api_models.py           # ✅ API 请求/响应模型
│   │   ├── user_profile.py        # 用户档案模型
│   │   ├── food_item.py          # 食物项模型
│   │   ├── exercise_item.py      # 运动项模型
│   │   └── analysis_result.py    # 分析结果模型
│   ├── api/               # ✅ API 路由
│   │   ├── __init__.py
│   │   ├── router_health.py        # 健康检查
│   │   ├── router_analyze.py       # 流式分析
│   │   ├── router_users.py         # 用户管理
│   │   └── router_requests.py      # 请求管理
│   ├── storage/           # ✅ 存储层（可扩展）
│   │   ├── __init__.py             # 存储工厂
│   │   ├── json_storage.py       # JSON 文件存储
│   │   └── database.py          # MySQL 数据库存储
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── logger.py            # 日志系统配置
│       ├── llm_client.py        # LLM 客户端封装
│       ├── image_utils.py       # 图片处理工具
│       ├── request_manager.py   # ✅ 请求管理器（并发控制）
│       └── sse_utils.py        # ✅ SSE 事件工具
├── frontend/              # ✅ Vue3 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── api/client.ts         # API 客户端
│   │   ├── views/
│   │   │   ├── Home.vue         # 首页
│   │   │   ├── Analyze.vue      # 分析页面（核心）
│   │   │   ├── Users.vue        # 用户管理
│   │   │   └── Requests.vue     # 请求管理
│   │   └── router/index.ts      # Vue Router
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
└── data/                  # 数据目录（JSON存储时使用）
    ├── users/             # 用户档案存储目录
    └── logs/              # 日志文件目录
```

---

## ⚙️ 环境变量配置

```env
# ============== LLM 配置 ==============
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=doubao-seed-2.0-pro

# ============== 服务配置 ==============
HOST=0.0.0.0
PORT=8083
WORKERS=2
LOG_LEVEL=INFO
DEBUG=false

# ============== CORS 配置 ==============
CORS_ORIGINS=*

# ============== 并发控制 ==============
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT_SECONDS=120
COMPLETED_REQUEST_TTL_HOURS=1

# ============== 认证配置 ==============
API_KEY_ENABLED=false
# API_KEY=your_secret_api_key_here

# ============== 限流配置 ==============
RATE_LIMIT_ENABLED=false
RATE_LIMIT_PER_MINUTE=30

# ============== 数据存储 ==============
# 存储类型: json / mysql
STORAGE_TYPE=mysql
DATA_DIR=./data
USERS_DIR=./data/users
LOGS_DIR=./data/logs

# ============== MySQL 数据库 ==============
DB_HOST=172.32.6.110
DB_PORT=30308
DB_USER=root
DB_PASSWORD=root
DB_NAME=db_slimcheck
DB_CHARSET=utf8mb4
```

---

## 🗄️ 数据存储

### 存储方式切换

通过 `.env` 配置文件切换：

```ini
# MySQL 数据库存储（推荐生产环境）
STORAGE_TYPE=mysql

# 或者 JSON 文件存储（适合开发/单机部署）
STORAGE_TYPE=json
```

### MySQL 数据库模式

**数据库表结构** (`tb_user_profiles`)：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT | 主键自增 |
| `person_id` | VARCHAR(32) | 用户唯一标识（UUID短码） |
| `name` | VARCHAR(100) | 用户姓名 |
| `gender` | ENUM | 性别：male/female |
| `age` | INT | 年龄 |
| `height_cm` | FLOAT | 身高（厘米） |
| `weight_kg` | FLOAT | 体重（公斤） |
| `activity_level` | ENUM | 活动水平 |
| `bmi` | FLOAT | 身体质量指数 |
| `bmr` | FLOAT | 基础代谢率（千卡/天） |
| `daily_calorie_needs` | FLOAT | 每日所需卡路里 |
| `health_assessment` | VARCHAR(200) | 健康评估结论 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |

**字段名注意事项**：
- 用户注册接口字段：`height_cm`, `weight_kg`（不是 `height`, `weight`）
- 所有 API 响应都使用 `height_cm`, `weight_kg` 格式

---

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

---

## 🤖 智能体使用的计算公式

### BMI 计算公式

```
BMI = 体重(kg) / (身高(m))^2
```

### 基础代谢率 (BMR) - Mifflin-St Jeor 公式

- **男性**: `BMR = 10 × 体重(kg) + 6.25 × 身高(cm) - 5 × 年龄 + 5`
- **女性**: `BMR = 10 × 体重(kg) + 6.25 × 身高(cm) - 5 × 年龄 - 161`

### 每日所需卡路里

```
每日所需 = BMR × 活动系数
```

活动系数：
- 久坐: 1.2
- 轻度运动: 1.375
- 中度运动: 1.55 **默认**
- 活跃运动: 1.725
- 非常活跃: 1.9

---

## 🔒 生产环境建议

1. **启用认证**: 设置 `API_KEY_ENABLED=true` 并配置 `API_KEY`
2. **配置 CORS**: 设置 `CORS_ORIGINS` 为你的前端域名
3. **启用限流**: 设置 `RATE_LIMIT_ENABLED=true`
4. **使用 MySQL**: 生产环境建议使用 MySQL 存储，替代 JSON 文件
5. **使用 HTTPS**: 配置反向代理（Nginx/Caddy）提供 HTTPS
6. **监控告警**: 接入 Prometheus + Grafana 监控
7. **日志收集**: 结构化日志输出到 Loki/ELK

---

## 🧪 测试

```bash
# 健康检查
curl http://localhost:8083/api/v1/health

# 注册用户
curl -X POST http://localhost:8083/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"gender":"male","age":30,"height_cm":175,"weight_kg":75}'

# 列出用户
curl http://localhost:8083/api/v1/users

# 流式分析（使用浏览器或 EventSource 客户端）
```

---

## 📚 相关文档

- **[API_SERVER.md](./API_SERVER.md)** - API 服务详细文档
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - 完整 API 接口文档
- **[DESIGN.md](./DESIGN.md)** - 系统设计文档
- **[Frontend README](./frontend/README.md)** - 前端开发文档

---

## License

MIT
