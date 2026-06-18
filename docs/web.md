---
layout: default
title: Web 界面指南
---

# 🌐 Web 管理界面

Ledger 提供开箱即用的 Web 管理界面，基于 Flask + Bootstrap 5，响应式设计，手机/平板/电脑均可用。

---

## 启动

### 直接运行

```bash
# 安装依赖
pip install flask flask-cors

# 启动
python web/run.py

# 访问
open http://localhost:5800
```

### Docker 方式

```bash
docker run -d --name ledger -p 5800:5800 -v ./data:/data --restart unless-stopped zouzhenglu/ledger:latest
open http://localhost:5800
```

---

## 页面功能

### 📊 概览页

![](https://via.placeholder.com/800x400?text=Dashboard+Preview)

- 收支汇总卡片（总收入 / 总支出 / 结余）
- 月度收支趋势图
- 最近交易列表
- 快捷记账入口

### 📋 交易页

- 完整交易记录表格
- 按日期 / 类型 / 类别 / 账户排序
- 关键词搜索
- 多条件筛选（日期范围 / 类别 / 账户）
- 新增 / 编辑 / 删除交易

### 💰 预算页

- 当月所有类别预算列表
- 实时进度条（已用 / 预算）
- 超支预警（红色进度条）
- 新增 / 编辑预算

### 🏷 类别页

- 类别 / 子类别层级展示
- 各类别消费笔数和金额统计

### 📈 统计页

- 按类别分组统计（饼图 / 列表）
- 按账户分组统计
- 按月趋势统计

---

## 配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `WEB_HOST` | 监听地址 | `0.0.0.0` |
| `WEB_PORT` | 端口 | `5800` |
| `WEB_DEBUG` | 调试模式 | `false` |
| `LEDGER_DB_PATH` | 数据库路径 | `./ledger.db` |

## API 端点

Web 前端通过以下 API 与后端交互：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/info` | GET | 系统信息 |
| `/api/transactions` | GET | 交易列表 |
| `/api/transactions` | POST | 新增交易 |
| `/api/transactions/<id>` | PUT | 更新交易 |
| `/api/transactions/<id>` | DELETE | 软删除交易 |
| `/api/transactions/<id>/restore` | POST | 恢复交易 |
| `/api/transactions/<id>/hard` | DELETE | 物理删除 |
| `/api/summary` | GET | 收支汇总 |
| `/api/statistics` | GET | 统计分析 |
| `/api/budgets` | GET | 预算列表 |
| `/api/budgets` | POST | 设置预算 |
| `/api/categories` | GET | 类别列表 |
| `/api/accounts` | GET | 账户列表 |

完整 API 文档见 [api.md](api.md)。
