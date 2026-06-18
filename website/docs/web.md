---
sidebar_position: 13
---

# 🌐 Web 管理界面

Ledger 提供开箱即用的 Web 管理界面，基于 **Flask + Bootstrap 5**，响应式设计，手机 / 平板 / 电脑均可用。

## 启动

### 直接运行

```bash
pip install flask flask-cors
python web/run.py
```

访问 [http://localhost:5800](http://localhost:5800)

### Docker

```bash
docker run -d --name ledger -p 5800:5800 -v ./data:/data --restart unless-stopped zouzhenglu/ledger:latest
```

访问 [http://localhost:5800](http://localhost:5800)

## 功能页面

### 📊 概览 Dashboard

- 收支汇总卡片（总收入 / 总支出 / 结余）
- 月度收支趋势图
- 最近交易列表
- 快捷记账入口

### 📋 交易管理

- 完整交易记录表格，支持多字段排序
- 关键词搜索 + 多条件筛选（日期 / 类别 / 账户）
- 新增 / 编辑 / 软删除交易

### 💰 预算仪表盘

- 当月所有类别预算列表
- 实时进度条（已用额度 / 预算总额）
- 超支预警（红色进度条标识）
- 新增 / 编辑预算

### 🏷 类别总览

- 类别 / 子类别层级展示
- 各类别消费笔数和金额统计

### 📈 统计图表

- 按类别分组统计
- 按账户分组统计
- 按月趋势统计

## 配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `WEB_HOST` | 监听地址 | `0.0.0.0` |
| `WEB_PORT` | 端口 | `5800` |
| `WEB_DEBUG` | 调试模式 | `false` |
| `LEDGER_DB_PATH` | 数据库路径 | `./ledger.db` |

:::tip 端口说明
默认使用 5800 端口，避免被其他常见服务（5000/3000）占用。
:::
