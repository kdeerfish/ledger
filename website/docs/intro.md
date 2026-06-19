---
sidebar_position: 1
---

# 📒 Ledger 文档站

**Ledger** 是一个个人记账系统，支持 CLI 命令行、React Web 界面、AI Agent 集成，可通过 Docker 一键部署。

**当前版本：v0.1.0** — 首个公开发布版本。

## ✨ 功能总览

### 📊 交易管理

| 功能 | 说明 |
|------|------|
| **记账** | 添加 / 编辑 / 软删除 / 恢复 / 物理删除 |
| **标签** | 多标签创建/关联/筛选/统计，颜色标记 |
| **搜索** | 关键词搜索（备注/类别/商家/全局） |
| **筛选** | 按类别 / 子类别 / 账户 / 商家 / 项目 / 成员 / 标签 / 日期范围 |
| **导入** | 随手记 CSV 一键导入，自动去重 |
| **导出** | CSV / JSON 格式导出 |

### 💰 预算管理

| 功能 | 说明 |
|------|------|
| **预算设置** | 按月 / 类别 / 账户 / 成员 / 项目 设置预算 |
| **进度跟踪** | 实时计算已用额度，进度条展示，超支预警 |
| **预算模板** | 创建 → 列表 → 更新 → 删除 → 一键应用 |
| **智能推荐** | 基于历史记录自动推荐预算模板 |

### 📈 统计分析

| 功能 | 说明 |
|------|------|
| **收支汇总** | 按年 / 月查看总收入、总支出、结余、日均支出 |
| **多维度统计** | 按类别 / 子类别 / 账户 / 商家 / 项目 / 成员 / 月 / 标签 / 类型 |
| **交互图表** | 柱状图 / 折线图 / 环形图 / 饼图，点击跳转交易筛选 |
| **累计趋势** | 累计收入/支出折线图 |
| **数据交叉分析** | 商家→类别、账户→商家 关联分析（供 AI Agent 学习） |

### 📋 记账模板

| 功能 | 说明 |
|------|------|
| **模板创建** | 含类别/子类别/账户/商家/标签，一键记账 |
| **使用统计** | 按使用频次排序，常用模板优先展示 |
| **Web 快速选择** | 记一笔时顶部显示常用模板 |

### 🤖 AI Agent

| 功能 | 说明 |
|------|------|
| **JSON 接口** | 通过 `ledger_cli.py` 接收 JSON 参数 |
| **技能包** | 为 [picoclaw](https://github.com/zouzhenglu/picoclaw) 提供技能文档 |
| **数据学习** | `analyze` 命令输出结构化数据摘要供 Agent 学习用户习惯 |

### 🌐 Web 界面

| 功能 | 说明 |
|------|------|
| **概览 Dashboard** | 收支卡片 + 月度柱状图 + 累计折线图 + 类别环形图(可点击) |
| **交易管理** | 多维筛选(类型/类别/账户/日期/标签) + 表格 + 分页 + 编辑/删除 |
| **记一笔** | 模板选择 + 字段自动建议 + 子类别快速选择 + 标签选择器 |
| **预算仪表盘** | 总览 + 进度条 + 超支预警 + 执行明细表 |
| **类别+标签** | 类别层级统计 + 标签创建/颜色管理 |
| **统计图表** | 9种分组 × 3种图表，点击跳转交易筛选 |

## 🐳 快速部署

```bash
# 拉取镜像（推荐 Docker Hub）
docker pull zouzhenglu/ledger:latest

# 启动容器
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger:latest

# 访问
open http://localhost:5800
```

## 📦 镜像仓库

| 仓库 | 拉取命令 | 速度 |
|------|----------|------|
| **Docker Hub**（主） | `docker pull zouzhenglu/ledger:latest` | 🌍 全球 |
| [ghcr.io](https://github.com/kdeerfish/ledger/pkgs/container/ledger) | `docker pull ghcr.io/kdeerfish/ledger:latest` | 🌍 备选 |
| 阿里云容器镜像服务 | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` | 🇨🇳 国内最快 |

## 🌟 项目信息

| 项目 | 链接 |
|------|------|
| GitHub 仓库 | [kdeerfish/ledger](https://github.com/kdeerfish/ledger) |
| 问题反馈 | [Issues](https://github.com/kdeerfish/ledger/issues) |
| Docker Hub | [zouzhenglu/ledger](https://hub.docker.com/r/zouzhenglu/ledger) |
| 许可 | MIT |
