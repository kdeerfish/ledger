---
sidebar_position: 13
---

# 🌐 Web 管理界面

Ledger 提供开箱即用的 Web 管理界面，基于 **React + Vite + Chart.js**，响应式设计，手机 / 平板 / 电脑均可用。

## 启动

### 生产模式（一个端口 :5800）

```bash
# 1. 安装 Python 依赖
pip install flask flask-cors

# 2. 构建前端（仅首次或升级时需要）
cd frontend && npm install && npm run build && cd ..

# 3. 启动（Flask 直接服务构建好的前端）
python web/run.py
```

访问 [http://localhost:5800](http://localhost:5800)

### Docker（推荐）

```bash
docker run -d --name ledger -p 5800:5800 -v ./data:/data --restart unless-stopped zouzhenglu/ledger:latest
```

Docker 镜像使用多阶段构建，自动编译前端，最终镜像不含 Node.js。

### 开发模式（有热更新）

```bash
# 终端 1: Flask 后端（调试模式，自动代理前端请求到 Vite）
WEB_DEBUG=true python web/run.py

# 终端 2: Vite 开发服务器
cd frontend && npm run dev

# 访问 http://localhost:5800 — 自动代理到 Vite，改代码页面自动刷新
```

或使用 VS Code launch.json 的 **"Full Stack Dev"** compound 配置一键启动。

## 功能页面

### 📊 概览 Dashboard

- 收支汇总卡片（总收入 / 总支出 / 结余 / 日均支出）
- 月度收支趋势柱状图
- 累计收入/支出折线图
- 支出类别占比环形图（点击跳转到交易页并筛选该类别）
- 最近交易列表（点击跳转详情）

### 📋 交易管理

- 完整交易记录表格，支持标签展示
- 关键词搜索 + 多条件筛选（类型 / 类别 / 账户 / 日期范围 / 标签点击筛选）
- 记一笔弹窗：模板选择 → 字段自动建议 → 子类别快速选择 → 标签选择器 → 保存
- 编辑 / 软删除

### 💰 预算仪表盘

- 总预算 / 已支出 / 剩余 总览卡片
- 所有类别预算卡片（进度条 + 超支预警）
- 预算执行明细表（类别 / 预算 / 已用 / 剩余 / 进度百分比）

### 🏷 类别与标签

- 类别 / 子类别层级展示
- 各类别消费笔数和金额统计
- 标签管理：创建 / 颜色选择 / 删除
- 标签使用次数统计

### 📈 统计图表

- 支持 9 种分组维度：类别 / 子类别 / 账户 / 商家 / 项目 / 成员 / 月 / 标签 / 类型
- 3 种图表类型：环形图 / 饼图 / 柱状图
- 收入/支出双图展示
- **点击图表任意部分 → 自动跳转到交易页并带入筛选条件**
- 数据明细表含进度条占比

## 配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `WEB_HOST` | 监听地址 | `0.0.0.0` |
| `WEB_PORT` | 端口 | `5800` |
| `WEB_DEBUG` | 调试模式（开启后代理到 Vite 热更新） | `false` |
| `LEDGER_DB_PATH` | 数据库路径 | `./ledger.db` |

:::tip 一个端口搞定
生产环境 `WEB_DEBUG=false` 时 Flask 直接服务构建好的静态文件，无需 Vite。
开发环境 `WEB_DEBUG=true` 时 Flask 自动代理页面请求到 Vite 开发服务器（:5173），获得热更新能力。
全通过 `:5800` 访问。
:::
