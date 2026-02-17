# AURUM Dashboard - 前端项目

黄金量化交易系统的Web Dashboard，基于React + Next.js + TypeScript构建。

## 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: TailwindCSS
- **图表**: Recharts + Lightweight Charts
- **状态管理**: Zustand
- **数据请求**: Axios + SWR
- **实时通信**: WebSocket

## 项目结构

```
frontend/
├── app/                    # Next.js App Router页面
│   ├── dashboard/         # Dashboard首页
│   ├── strategies/        # 策略配置页面
│   ├── backtest/          # 回测结果页面
│   ├── analytics/         # 数据分析页面
│   ├── layout.tsx         # 根布局
│   └── globals.css        # 全局样式
├── components/            # 可复用组件
├── hooks/                 # 自定义Hooks
├── stores/                # Zustand状态管理
├── types/                 # TypeScript类型定义
├── utils/                 # 工具函数
└── lib/                   # 第三方库配置
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 配置环境变量

复制 `.env.local.example` 为 `.env.local` 并配置：

```bash
cp .env.local.example .env.local
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
npm start
```

## 核心功能

### 1. Dashboard首页
- 账户权益实时显示
- 持仓监控
- 交易信号展示
- 实时行情图表

### 2. 策略配置
- 多代理权重调整
- 风险参数设置
- 策略启停控制

### 3. 回测结果
- 收益曲线可视化
- 交易统计分析
- 详细交易记录

### 4. 实时数据
- WebSocket实时推送
- 价格/信号/持仓更新
- 自动重连机制

## 开发规范

### 代码风格
- 使用TypeScript严格模式
- 遵循ESLint规则
- 组件使用函数式写法

### 命名规范
- 组件: PascalCase (如 `DashboardPage`)
- 函数: camelCase (如 `handleSubmit`)
- 常量: UPPER_SNAKE_CASE (如 `API_BASE_URL`)

### 提交规范
- feat: 新功能
- fix: 修复bug
- style: 样式调整
- refactor: 重构代码
- docs: 文档更新

## API对接

后端API地址配置在 `.env.local` 中：

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

API客户端位于 `utils/api.ts`，包含所有接口方法。

## 部署

### Vercel部署（推荐）

```bash
npm install -g vercel
vercel
```

### Docker部署

```bash
docker build -t aurum-dashboard .
docker run -p 3000:3000 aurum-dashboard
```

## 性能优化

- 使用Next.js图片优化
- 代码分割和懒加载
- SWR缓存策略
- WebSocket连接池

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 许可证

MIT License
