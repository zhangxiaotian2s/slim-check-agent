# SlimCheck API 文档

## 目录
- [基础信息](#基础信息)
- [统一响应格式](#统一响应格式)
- [健康检查接口](#健康检查接口)
- [用户管理接口](#用户管理接口)
- [分析接口](#分析接口)
- [请求管理接口](#请求管理接口)
- [前端对接指南](#前端对接指南)

---

## 基础信息

### 服务器信息
| 项 | 值 |
|----|----|
| **基础 URL** | `http://localhost:8083/api/v1` |
| **文档地址** | `http://localhost:8083/docs` (Swagger UI) |
| **Redoc 文档** | `http://localhost:8083/redoc` |
| **OpenAPI Schema** | `http://localhost:8083/openapi.json` |

### 通用请求头
| 头名 | 类型 | 说明 |
|------|------|------|
| `Content-Type` | string | `application/json` |
| `X-Request-ID` | string | 可选，请求追踪 UUID |

---

## 统一响应格式

所有非流式接口都采用统一的响应格式，前端可以统一处理：

```typescript
interface ApiResponse<T> {
  code: 0 | -1;   // 0 = 成功, -1 = 失败
  data: T | null; // 响应数据主体，失败时为 null
  msg: string;     // 成功或失败的消息描述
}
```

### 成功响应示例
```json
{
  "code": 0,
  "data": {
    "person_id": "a1b2c3d4",
    "name": "张三",
    "age": 30
  },
  "msg": "用户注册成功"
}
```

### 失败响应示例
```json
{
  "code": -1,
  "data": null,
  "msg": "用户不存在"
}
```

---

## 健康检查接口

### 1. 基础健康检查
用于 liveness 探针，检查服务是否运行。

**接口地址**: `GET /api/v1/health`

**请求参数**: 无

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "status": "healthy",
    "timestamp": "2026-04-22T10:30:00.000000",
    "version": "1.0.0"
  },
  "msg": "服务运行正常"
}
```

---

### 2. 就绪检查
用于 readiness 探针，检查服务是否就绪。

**接口地址**: `GET /api/v1/ready`

**请求参数**: 无

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "status": "ready",
    "timestamp": "2026-04-22T10:30:00.000000",
    "version": "1.0.0"
  },
  "msg": "服务就绪"
}
```

---

## 用户管理接口

### 1. 注册用户
创建个人健康档案，计算 BMI、基础代谢率、每日所需卡路里。

**接口地址**: `POST /api/v1/users/register`

**请求体**:
```json
{
  "gender": "male",
  "age": 30,
  "height": 175.0,
  "weight": 75.0,
  "activity_level": "moderate",
  "name": "张三"
}
```

**请求参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `gender` | string | ✅ | 性别: `male` (男) / `female` (女) |
| `age` | int | ✅ | 年龄: 1-150 |
| `height` | float | ✅ | 身高（厘米）: 0-300 |
| `weight` | float | ✅ | 体重（公斤）: 0-500 |
| `activity_level` | string | ❌ | 活动水平，默认: `moderate` |
| `name` | string | ❌ | 姓名，最大 100 字符 |

**活动水平说明**:
| 值 | 说明 | 活动系数 |
|----|------|----------|
| `sedentary` | 久坐（很少运动） | 1.2 |
| `light` | 轻度运动（每周1-3次） | 1.375 |
| `moderate` | 中度运动（每周3-5次） | 1.55 |
| `active` | 活跃运动（每周6-7次） | 1.725 |
| `very_active` | 非常活跃（每日高强度） | 1.9 |

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "person_id": "a1b2c3d4",
    "name": "张三",
    "gender": "male",
    "age": 30,
    "height_cm": 175.0,
    "weight_kg": 75.0,
    "activity_level": "moderate",
    "bmi": 24.49,
    "bmr": 1698.75,
    "daily_calorie_needs": 2633.06,
    "health_assessment": "超重，建议控制热量摄入并增加运动",
    "created_at": "2026-04-22T10:30:00.000000"
  },
  "msg": "用户注册成功"
}
```

**失败响应示例**:
```json
{
  "code": -1,
  "data": null,
  "msg": "参数验证错误: age 必须大于等于 1"
}
```

---

### 2. 查询用户档案
查询指定用户的完整健康档案。

**接口地址**: `GET /api/v1/users/{person_id}`

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `person_id` | string | ✅ | 用户 ID |

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "person_id": "a1b2c3d4",
    "name": "张三",
    "gender": "male",
    "age": 30,
    "height_cm": 175.0,
    "weight_kg": 75.0,
    "activity_level": "moderate",
    "bmi": 24.49,
    "bmr": 1698.75,
    "daily_calorie_needs": 2633.06,
    "health_assessment": "超重，建议控制热量摄入并增加运动",
    "created_at": "2026-04-22T10:30:00.000000"
  },
  "msg": "查询成功"
}
```

**失败响应（用户不存在）**:
```json
{
  "code": -1,
  "data": null,
  "msg": "用户不存在"
}
```

---

### 3. 列出所有用户
获取所有已注册用户的列表。

**接口地址**: `GET /api/v1/users`

**请求参数**: 无

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "total": 2,
    "users": [
      {
        "person_id": "a1b2c3d4",
        "name": "张三",
        "gender": "male",
        "age": 30,
        "height_cm": 175.0,
        "weight_kg": 75.0,
        "activity_level": "moderate",
        "bmi": 24.49,
        "bmr": 1698.75,
        "daily_calorie_needs": 2633.06,
        "health_assessment": "超重，建议控制热量摄入并增加运动",
        "created_at": "2026-04-22T10:30:00.000000"
      },
      {
        "person_id": "e5f6g7h8",
        "name": "李四",
        "gender": "female",
        "age": 28,
        "height_cm": 165.0,
        "weight_kg": 55.0,
        "activity_level": "light",
        "bmi": 20.2,
        "bmr": 1285.5,
        "daily_calorie_needs": 1767.56,
        "health_assessment": "正常，继续保持",
        "created_at": "2026-04-21T09:00:00.000000"
      }
    ]
  },
  "msg": "获取用户列表成功"
}
```

---

### 4. 删除用户
删除指定用户的档案。

**接口地址**: `DELETE /api/v1/users/{person_id}`

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `person_id` | string | ✅ | 要删除的用户 ID |

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "person_id": "a1b2c3d4"
  },
  "msg": "用户已删除"
}
```

**失败响应（用户不存在）**:
```json
{
  "code": -1,
  "data": null,
  "msg": "用户不存在"
}
```

---

## 分析接口

### 1. 流式分析接口（核心接口）
基于 SSE (Server-Sent Events) 的流式分析，实时返回分析状态和中间结果。

> **注意**: SSE 流式接口不使用统一响应格式，每个事件独立推送。

**接口地址**: `POST /api/v1/analyze/stream`

**Content-Type**: `text/event-stream`

**请求体**:
```json
{
  "input_type": "text_only",
  "text": "早餐吃了一个包子，喝了一杯豆浆，午饭后慢跑了30分钟",
  "person_id": "a1b2c3d4",
  "content_type_hint": "both"
}
```

**请求参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `input_type` | string | ✅ | 输入类型: `text_only` / `image` / `image_with_text` |
| `text` | string | ✅/❌ | 文本描述（`text_only` 和 `image_with_text` 必需） |
| `image_base64` | string | ✅/❌ | base64 编码的图片（`image` 和 `image_with_text` 必需） |
| `person_id` | string | ❌ | 用户 ID，用于个性化分析 |
| `content_type_hint` | string | ❌ | 内容类型提示: `diet` / `exercise` / `both` |

---

#### SSE 事件类型说明

| 事件类型 | 说明 |
|---------|------|
| `status` | 阶段更新，包含进度百分比 |
| `thinking` | 大模型思考过程内容，用于前端展示思考链路 |
| `partial_result` | 中间结果数据 |
| `error` | 错误信息 |
| `complete` | 分析完成 |
| `cancelled` | 请求被取消 |

---

##### 1) `thinking` - 思考过程事件
```
event: thinking
data: {
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "analyze_diet",
  "content": "识别到 3 种食物: 猪肉包子, 豆浆, 鸡蛋\n饮食总热量: 450 kcal\n正在计算蛋白质、碳水化合物、脂肪宏量营养素...",
  "timestamp": "2026-04-22T10:30:03.000000"
}
```
用于在前端展示 AI 的实时思考过程，增强用户体验。

---

#### 事件流示例

##### 1) status - 路由输入阶段
```
event: status
data: {
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "route_input",
  "message": "识别输入类型...",
  "progress": 10,
  "timestamp": "2026-04-22T10:30:00.000000"
}
```

##### 2) partial_result - 饮食分析结果
```
event: partial_result
data: {
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "food_items",
  "data": {
    "foods": [
      {
        "name": "猪肉包子",
        "calories": 250,
        "protein_g": 8.5,
        "carbs_g": 35.2,
        "fat_g": 8.8,
        "estimated_grams": 100
      },
      {
        "name": "豆浆",
        "calories": 80,
        "protein_g": 4.2,
        "carbs_g": 10.5,
        "fat_g": 1.8,
        "estimated_grams": 250
      }
    ],
    "total_calories": 330
  },
  "timestamp": "2026-04-22T10:30:03.000000"
}
```

##### 3) partial_result - 运动分析结果
```
event: partial_result
data: {
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "exercise_items",
  "data": {
    "exercises": [
      {
        "type": "慢跑",
        "duration_minutes": 30,
        "calories_burned": 280
      }
    ],
    "total_calories_burned": 280
  },
  "timestamp": "2026-04-22T10:30:05.000000"
}
```

##### 4) complete - 分析完成
```
event: complete
data: {
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true,
  "duration_ms": 7500,
  "final_result": {
    "summary": "总共摄入 330 大卡，运动消耗 280 大卡",
    "diet": {
      "total_calories": 330,
      "food_items": []
    },
    "exercise": {
      "total_calories_burned": 280,
      "exercise_items": []
    }
  },
  "timestamp": "2026-04-22T10:30:07.500000"
}
```

---

## 请求管理接口

### 1. 查询请求状态
查询指定分析请求的当前状态。

**接口地址**: `GET /api/v1/requests/{request_id}/status`

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `request_id` | string | ✅ | 请求 ID |

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "current_stage": "analyze_diet",
    "created_at": "2026-04-22T10:30:00.000000",
    "started_at": "2026-04-22T10:30:00.500000",
    "completed_at": null,
    "duration_ms": null,
    "error": null
  },
  "msg": "查询成功"
}
```

**状态说明**:
| 值 | 说明 |
|----|------|
| `pending` | 等待中（排队） |
| `running` | 执行中 |
| `completed` | 已完成 |
| `cancelled` | 已取消 |
| `failed` | 失败 |

---

### 2. 取消请求
取消正在进行的分析请求。

**接口地址**: `POST /api/v1/requests/{request_id}/cancel`

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `request_id` | string | ✅ | 要取消的请求 ID |

**成功响应**:
```json
{
  "code": 0,
  "data": null,
  "msg": "请求已取消"
}
```

**失败响应示例**:
```json
{
  "code": -1,
  "data": null,
  "msg": "请求无法取消，当前状态: completed"
}
```

---

### 3. 列出所有请求
获取所有请求列表，可按状态过滤。

**接口地址**: `GET /api/v1/requests`

**请求参数**: 无

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "total": 2,
    "requests": [
      {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "running",
        "current_stage": "analyze_diet",
        "created_at": "2026-04-22T10:30:00.000000",
        "started_at": "2026-04-22T10:30:00.500000",
        "completed_at": null,
        "duration_ms": null,
        "error": null
      },
      {
        "request_id": "660e8400-e29b-41d4-a716-446655440001",
        "status": "completed",
        "created_at": "2026-04-22T10:25:00.000000",
        "started_at": "2026-04-22T10:25:00.500000",
        "completed_at": "2026-04-22T10:25:08.000000",
        "duration_ms": 7500,
        "error": null
      }
    ],
    "stats": {
      "total_requests": 2,
      "pending": 0,
      "running": 1,
      "completed": 1,
      "cancelled": 0,
      "failed": 0,
      "avg_duration_ms": 7500,
      "success_rate": 1.0
    }
  },
  "msg": "获取请求列表成功"
}
```

---

### 4. 请求统计
获取请求统计信息。

**接口地址**: `GET /api/v1/requests/stats`

**请求参数**: 无

**成功响应**:
```json
{
  "code": 0,
  "data": {
    "total_requests": 156,
    "pending": 2,
    "running": 3,
    "completed": 145,
    "cancelled": 4,
    "failed": 2,
    "avg_duration_ms": 7250,
    "success_rate": 0.9615
  },
  "msg": "获取统计信息成功"
}
```

---

## 前端对接指南

### TypeScript 基础封装

```typescript
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8083/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 统一响应接口
export interface ApiResponse<T = any> {
  code: 0 | -1
  data: T | null
  msg: string
}

// 用户档案
export interface UserProfile {
  person_id: string
  name?: string
  gender: 'male' | 'female'
  age: number
  height_cm: number
  weight_kg: number
  activity_level?: string
  bmi?: number
  bmr?: number
  daily_calorie_needs?: number
  health_assessment?: string
  created_at?: string
}

// 统一请求处理函数
async function request<T>(url: string, config?: any): Promise<ApiResponse<T>> {
  try {
    const response = await api.request<ApiResponse<T>>({ url, ...config })
    return response.data
  } catch (e: any) {
    return {
      code: -1,
      data: null,
      msg: e.response?.data?.msg || e.message || '请求失败'
    }
  }
}

// 用户 API
export const userApi = {
  register: (data: Partial<UserProfile>) => 
    request<UserProfile>('/users/register', { method: 'POST', data }),
  
  get: (personId: string) => 
    request<UserProfile>(`/users/${personId}`),
  
  list: () => 
    request<{ total: number; users: UserProfile[] }>('/users'),
  
  delete: (personId: string) => 
    request<null>(`/users/${personId}`, { method: 'DELETE' })
}
```

### 使用示例

```typescript
// 注册用户
const result = await userApi.register({
  gender: 'male',
  age: 30,
  height_cm: 175,
  weight_kg: 75,
  activity_level: 'moderate',
  name: '张三'
})

if (result.code === 0 && result.data) {
  console.log('注册成功:', result.data.person_id)
} else {
  console.error('注册失败:', result.msg)
}

// 获取用户列表
const listResult = await userApi.list()
if (listResult.code === 0 && listResult.data) {
  console.log('用户列表:', listResult.data.users)
}
```

### SSE 流式分析对接

```typescript
export interface StatusEvent {
  request_id: string
  stage: string
  message: string
  progress: number
  timestamp: string
}

export interface PartialResultEvent<T> {
  request_id: string
  type: string
  data: T
  timestamp: string
}

function streamAnalysis(
  requestData: any,
  handlers: {
    onStatus?: (event: StatusEvent) => void
    onPartialResult?: (event: PartialResultEvent<any>) => void
    onComplete?: () => void
    onError?: (error: string) => void
  }
): EventSource {
  const eventSource = new EventSource(
    `${API_BASE_URL}/analyze/stream`,
    { withCredentials: true }
  )

  eventSource.addEventListener('status', (e: any) => {
    const data = JSON.parse(e.data)
    handlers.onStatus?.(data)
  })

  eventSource.addEventListener('partial_result', (e: any) => {
    const data = JSON.parse(e.data)
    handlers.onPartialResult?.(data)
  })

  eventSource.addEventListener('complete', () => {
    eventSource.close()
    handlers.onComplete?.()
  })

  eventSource.addEventListener('error', (e: any) => {
    const data = JSON.parse(e.data)
    eventSource.close()
    handlers.onError?.(data.msg || '分析失败')
  })

  return eventSource
}
```

### 注意事项

1. **错误处理**: 始终检查 `code` 字段判断请求是否成功，不要仅依赖 HTTP 状态码
2. **空数据**: 失败时 `data` 字段为 `null`，访问前请先判断
3. **SSE 特殊处理**: 流式分析接口不使用统一响应格式，请单独处理
4. **字段命名**: 后端使用下划线命名（如 `height_cm`），请保持一致
5. **类型安全**: 建议为所有 API 响应定义完整的 TypeScript 类型

---

## 字段命名对照表

| 前端字段 | 后端字段 | 类型 | 说明 |
|---------|---------|------|------|
| height_cm | height_cm | number | 身高（厘米） |
| weight_kg | weight_kg | number | 体重（公斤） |
| daily_calorie_needs | daily_calorie_needs | number | 每日所需卡路里 |
| protein_g | protein_g | number | 蛋白质（克） |
| carbs_g | carbs_g | number | 碳水化合物（克） |
| fat_g | fat_g | number | 脂肪（克） |
| calories_burned | calories_burned | number | 卡路里消耗 |
| duration_minutes | duration_minutes | number | 运动时长（分钟） |
