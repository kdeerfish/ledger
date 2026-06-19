<div align="center">

# 📒 Ledger — 个人记账系统

**收支管理 · 预算规划 · 标签分类 · 多维统计 · React 仪表盘 · AI Agent 集成**

[![Docker Pulls](https://img.shields.io/docker/pulls/zouzhenglu/ledger?logo=docker&label=Docker%20Hub)](https://hub.docker.com/r/zouzhenglu/ledger)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/docker-publish.yml?branch=master&label=CI%2FCD&logo=github)](https://github.com/kdeerfish/ledger/actions)
[![GitHub Release](https://img.shields.io/github/v/release/kdeerfish/ledger?logo=github)](https://github.com/kdeerfish/ledger/releases)
[![License](https://img.shields.io/github/license/kdeerfish/ledger)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)

**🐳 [`docker pull zouzhenglu/ledger`](https://hub.docker.com/r/zouzhenglu/ledger) · [📖 完整文档](https://kdeerfish.github.io/ledger) · [🚀 快速启动](#-一分钟启动) · [🐙 GitHub](https://github.com/kdeerfish/ledger)**

</div>

---

## 🐳 一分钟启动


```bash
# 1. 拉取镜像
docker pull zouzhenglu/ledger

# 2. 启动容器
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger

# 3. 打开浏览器
open http://localhost:5800
```

> 数据库自动持久化在 `./data/ledger.db`，删容器不丢数据。

### docker-compose（推荐生产使用）

```bash
wget https://raw.githubusercontent.com/kdeerfish/ledger/master/docker-compose.yml
docker compose up -d
```

### 备选镜像仓库

| 仓库 | 拉取命令 | 适用场景 |
|------|----------|----------|
| **Docker Hub**（主） | `docker pull zouzhenglu/ledger` | 🌍 全球默认 |
| GitHub Container Registry | `docker pull ghcr.io/kdeerfish/ledger` | 🌍 开发者备选 |
| 阿里云容器镜像服务 | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger` | 🇨🇳 国内最快 |

### 容器内使用 CLI

```bash
# 查看最近交易
docker exec ledger python scripts/cli.py list

# 记一笔
docker exec ledger python scripts/cli.py add --type 支出 --amount 25.5 --category 食品 --account 微信

# 查看月度汇总
docker exec ledger python scripts/cli.py summary
```

---

## ✨ 功能总览

| 功能 | 说明 |
|------|------|
| ✅ **收支记账** | 添加 / 编辑 / 软删除 / 恢复 / 物理删除 |
| ✅ **标签分类** | 多标签创建 / 关联 / 筛选 / 统计，颜色标记 |
| ✅ **CSV 导入** | 随手记 CSV 一键导入，自动去重 |
| ✅ **搜索筛选** | 关键词 + 类别 / 账户 / 商家 / 标签 / 日期等多维筛选 |
| ✅ **统计分析** | 按类别 / 子类别 / 账户 / 商家 / 月 / 标签 / 类型 等 9 种分组 |
| ✅ **交互图表** | 柱状图 / 折线图 / 环形图 / 饼图，点击图表跳转筛选 |
| ✅ **预算管理** | 按月 / 类别设置预算，进度跟踪，超支预警 |
| ✅ **预算模板** | 创建模板、一键应用、智能推荐 |
| ✅ **记账模板** | 常用交易模板，一键记账，使用频次统计 |
| ✅ **数据导出** | CSV / JSON 格式导出 |
| ✅ **React 仪表盘** | 响应式 UI，手机 / 平板 / PC 均可用 |
| ✅ **AI Agent 集成** | 为 LLM Agent 提供 JSON API + 技能文档 |
| ✅ **Docker 多仓库** | CI/CD 自动推送 Docker Hub / ghcr.io / 阿里云 |

---

## 🌐 Web 管理界面

启动后访问 http://localhost:5800：

| 页面 | 功能 |
|------|------|
| **概览** | 收支卡片 + 月度柱状图 + 累计折线图 + 类别环形图（可点击筛选） |
| **交易** | 多维筛选表格 + 分页 + 编辑 / 删除 |
| **记一笔** | 模板选择 + 字段自动建议 + 子类别 + 标签选择器 |
| **预算** | 总览卡片 + 类别进度条 + 执行明细表 |
| **类别+标签** | 类别层级统计 + 标签创建 / 颜色管理 |
| **统计** | 9 种分组 × 3 种图表，点击跳转交易筛选 |

---

## 📖 CLI 命令速查

```bash
# 交易管理
python scripts/cli.py add      --type 支出 --amount 100 --category 食品 --account 微信
python scripts/cli.py list
python scripts/cli.py search   --keyword 午餐
python scripts/cli.py filter   --category 食品 --start_date 2026-01-01

# 统计分析
python scripts/cli.py summary
python scripts/cli.py stats    --group_by category

# 预算
python scripts/cli.py budget_set           --category 食品 --amount 1000
python scripts/cli.py budget_check
python scripts/cli.py budget_template_suggest

# 记账模板
python scripts/cli.py template_create      --template_name "通勤" ...
python scripts/cli.py template_apply       --template_id 1

# 数据导入导出
python scripts/cli.py import_csv           --file data.csv
python scripts/cli.py export               --output report.csv
```

> 完整 CLI 参考见 [📖 完整文档](https://kdeerfish.github.io/ledger/docs/cli/transactions)。

---

## 🛠 开发

### 环境要求

- Python 3.10+
- Node.js 20+（仅前端开发时需要）
- Git

### 快速搭建

```bash
# 克隆
git clone https://github.com/kdeerfish/ledger.git
cd ledger

# 虚拟环境
python -m venv .venv
# source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate         # Windows

# 安装
pip install -e ".[dev,lint]"
cd frontend && npm install && cd ..
```

### 开发模式（前后端热更新）

```bash
# 终端 1：Flask 后端（调试模式）
WEB_DEBUG=true python web/run.py

# 终端 2：Vite 前端（热更新）
cd frontend && npm run dev

# 访问 http://localhost:5800
```

### 项目结构

```
ledger/
├── frontend/               # React + Vite 前端
├── ledger_modules/         # Python 核心业务（db / transactions / budgets / config）
├── web/                    # Flask API（app.py / run.py）
├── scripts/                # CLI 入口 + 工具脚本
├── tests/                  # pytest 测试套件
├── skills/                 # AI Agent 技能包
├── .github/workflows/      # CI/CD：测试 → 构建 → Docker 推送
└── website/                # Docusaurus 文档站
```

### 常用命令

| 命令 | 说明 |
|------|------|
| `make test` | 运行全部测试 |
| `make coverage` | 测试 + 覆盖率报告 |
| `make lint` | ruff 代码检查 |
| `make lint-fix` | 自动修复 |
| `make format` | 格式化代码 |

---

## 📦 版本

当前版本 **v0.1.0** — 首个公开发布版本。

查看 [Releases](https://github.com/kdeerfish/ledger/releases) 了解完整变更历史。

---

<div align="center">

[📖 完整文档](https://kdeerfish.github.io/ledger) · [🐛 问题反馈](https://github.com/kdeerfish/ledger/issues) · [📦 Docker Hub](https://hub.docker.com/r/zouzhenglu/ledger) · [MIT License](LICENSE)

</div>
