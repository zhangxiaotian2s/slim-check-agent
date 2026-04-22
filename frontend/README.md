# SlimCheck Frontend

基于 Vue 3 + Vite + TypeScript 构建的智能卡路里管理系统前端，采用 Webflow 设计风格。

## ✨ 功能特性

- 🏠 **首页** - 产品展示与核心功能介绍
- 🧠 **智能分析** - 基于 SSE 流式输出的实时卡路里分析
- 👤 **用户管理** - 用户档案注册和健康参数管理
- 📊 **请求监控** - 实时监控 API 请求状态和系统资源
- 🎨 **Webflow 设计** - 现代化的 UI 设计系统

## 🚀 快速开始

### 环境要求

- Node.js 18+
- npm 或 yarn

### 安装依赖

```bash
cd frontend

# 如果遇到 npm 权限问题，先运行
sudo chown -R 501:20 "/Users/zhangxiaotian/.npm"

# 安装依赖
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API 客户端封装
│   ├── views/
│   │   ├── Home.vue           # 首页
│   │   ├── Analyze.vue        # 智能分析页
│   │   ├── Users.vue          # 用户管理页
│   │   └── Requests.vue       # 请求监控页
│   ├── router/
│   │   └── index.ts           # 路由配置
│   ├── styles/
│   │   └── global.css         # 全局样式与设计系统
│   ├── App.vue                # 根组件
│   └── main.ts                # 入口文件
├── vite.config.ts             # Vite 配置
└── package.json               # 项目配置
```

## 🎨 设计系统

### 颜色

- **主色**: Webflow Blue (#146ef5)
- **成功**: Green (#00d722)
- **警告**: Orange (#ff6b00)
- **危险**: Red (#ee1d36)
- **中性**: Near Black (#080808), Gray 700 (#363636), Gray 300 (#ababab)

### 排版

- **标题**: 600 weight, 24px - 56px
- **正文**: 500 weight, 14px - 20px
- **标签**: Uppercase, 10px - 15px, wide letter-spacing

### 组件

- **Buttons**: 4px radius, translate(6px) hover effect
- **Cards**: 1px border, subtle shadow
- **Badges**: Tinted background, uppercase

## 🔧 配置说明

### API 代理

开发环境通过 Vite 代理转发到后端：

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8083',
    changeOrigin: true
  }
}
```

### 环境变量

复制 `.env.example` 为 `.env`：

```env
VITE_API_URL=/api/v1
```

## 📱 响应式断点

- **Mobile**: 479px
- **Tablet**: 768px
- **Desktop**: 992px

## 🤝 常见问题

### npm 权限问题

```bash
sudo chown -R 501:20 "/Users/zhangxiaotian/.npm"
```

### 后端连接失败

确保后端服务已启动在 8083 端口：

```bash
cd ..
./start.sh
# 或
uvicorn src.server:app --reload --port 8083
```
