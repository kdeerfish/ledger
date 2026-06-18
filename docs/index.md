---
layout: default
title: Ledger 文档
---

# 📒 Ledger 文档站

**Ledger** 是一个个人记账系统，支持 CLI 命令行、Web 界面、AI Agent 集成，可通过 Docker 一键部署。

---

## 📖 文档目录

| 文档 | 说明 |
|------|------|
| [📘 CLI 命令参考](cli.md) | 完整 CLI 命令列表与参数说明 |
| [🌐 Web 界面指南](web.md) | Web 管理界面功能与操作 |
| [🐳 Docker 部署](docker.md) | Docker 部署、三仓库拉取、docker-compose |
| [🔌 API 文档](api.md) | Flask RESTful API 端点参考 |
| [🛠 开发指南](development.md) | 环境搭建、测试、开发流程 |
| [🚀 快速开始](../README.md#-快速开始) | 一分钟上手（返回首页） |

---

## ✨ 功能总览

```
Ledger 个人记账系统
├── 📊 交易管理
│   ├── 添加 / 编辑 / 删除 / 恢复交易
│   ├── 关键词搜索（备注/类别/商家）
│   ├── 多条件筛选（类别/账户/成员/日期）
│   └── CSV 导入（随手记格式）/ CSV+JSON 导出
├── 📈 统计分析
│   ├── 收支汇总（按年/月）
│   ├── 多维度统计（类别/账户/月份）
│   └── 数据交叉分析（供 AI Agent 学习）
├── 💰 预算管理
│   ├── 按月/类别设置预算
│   ├── 多维度预算（账户/成员/项目/商家）
│   ├── 预算模板（创建/应用/智能推荐）
│   └── 实时进度跟踪与超支预警
├── 📋 记录模板
│   ├── 常用交易模板（一键记账）
│   ├── 使用频次统计
│   └── 智能推荐（基于历史行为）
├── 🌐 Web 界面
│   ├── 概览 Dashboard
│   ├── 交易列表 / 搜索 / 筛选
│   ├── 预算仪表盘
│   └── 统计图表
├── 🤖 AI Agent 集成
│   ├── JSON API 接口
│   └── picoclaw 技能包
└── 🐳 Docker 部署
    ├── Docker Hub
    ├── GitHub Container Registry
    └── 阿里云镜像服务（国内加速）
```

---

## 🐳 快速部署

```bash
# 拉取镜像（任意一个仓库）
docker pull zouzhenglu/ledger:latest
docker pull ghcr.io/kdeerfish/ledger:latest
docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest

# 启动
docker run -d --name ledger -p 5800:5800 -v ./data:/data --restart unless-stopped zouzhenglu/ledger:latest

# 访问
open http://localhost:5800
```

查看完整 [Docker 部署指南](docker.md)

---

## 🚀 一分钟上手（CLI）

```bash
# 安装
pip install -e ".[dev,lint]"

# 记一笔
python scripts/cli.py add --type 支出 --amount 100 --category 食品 --account 微信

# 查看
python scripts/cli.py list

# 汇总
python scripts/cli.py summary
```

查看完整 [CLI 命令参考](cli.md)

---

<div align="center">

[GitHub](https://github.com/kdeerfish/ledger) · [问题反馈](https://github.com/kdeerfish/ledger/issues)

</div>
