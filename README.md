<div align="center">

# 📒 Ledger — 个人记账系统

**收支管理 · 预算规划 · 标签分类 · 多维统计 · React Web 界面 · AI Agent 集成**

[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/docker-publish.yml?branch=master&label=CI%2FCD&logo=github)](https://github.com/kdeerfish/ledger/actions)
[![Docker Pulls](https://img.shields.io/docker/pulls/zouzhenglu/ledger?logo=docker)](https://hub.docker.com/r/zouzhenglu/ledger)
[![GitHub Release](https://img.shields.io/github/v/release/kdeerfish/ledger?logo=github)](https://github.com/kdeerfish/ledger/releases)
[![License](https://img.shields.io/github/license/kdeerfish/ledger)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-252%20passed-brightgreen)](https://github.com/kdeerfish/ledger/actions)

**[快速开始](#-快速开始) · [CLI 命令](#-cli-命令速查) · [Web 界面](#-web-管理界面) · [Docker 部署](#-docker-部署) · [📖 完整文档](https://kdeerfish.github.io/ledger)**

</div>

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| ✅ **收支记账** | 添加/编辑/软删除/恢复/物理删除交易记录 |
| ✅ **标签分类** | 多标签支持（创建/关联/筛选/统计），颜色标记 |
| ✅ **CSV 导入** | 随手记 CSV 一键导入，自动去重 |
| ✅ **搜索筛选** | 按关键词、类别、账户、商家、标签、日期范围搜索 |
| ✅ **统计分析** | 按类别/子类别/账户/商家/项目/成员/月/标签/类型 分组 |
| ✅ **交互图表** | 柱状图/折线图/环形图/饼图，点击图表跳转筛选 |
| ✅ **预算管理** | 按月/类别设置预算，实时进度跟踪，超支预警 |
| ✅ **预算模板** | 创建预算模板、一键应用、自动推荐 |
| ✅ **记账模板** | 常用交易模板（含标签），一键记账、使用频次统计 |
| ✅ **数据导出** | 导出为 CSV / JSON |
| ✅ **Web 界面** | React + Vite 响应式 UI，手机/平板/PC 均可用 |
| ✅ **AI Agent** | 为 picoclaw 等 AI Agent 提供 JSON API |
| ✅ **Docker 部署** | 多阶段构建，支持 Docker Hub / ghcr.io / 阿里云 三仓库 |

---

## 🚀 快速开始

```bash
# 1. 安装 Python 依赖
pip install -e ".[dev,lint]"

# 2. 配置（可选，留空用默认值）
cp .env.example .env

# 3. 导入随手记 CSV（可选）
python scripts/import_ledger.py data/sample/mymoney_data.csv

# 4. 记一笔支出
python scripts/cli.py add --type 支出 --amount 100 --category 食品 --account 微信

# 5. 查看最近交易
python scripts/cli.py list

# 6. 查看本月汇总
python scripts/cli.py summary
```

---

## 🌐 Web 管理界面

### 生产模式（不需要 Node.js）

```bash
# 1. 安装 Python 依赖
pip install flask flask-cors

# 2. 构建前端（仅首次或升级时需要）
cd frontend && npm install && npm run build && cd ..

# 3. 启动
python web/run.py
# 访问 http://localhost:5800
```

### 开发模式（有热更新）

```bash
# 终端 1: Flask 后端
WEB_DEBUG=true python web/run.py

# 终端 2: Vite 开发服务器
cd frontend && npm run dev

# 访问 http://localhost:5800（自动代理到 Vite 热更新）
```

或直接用 VS Code 的 **"Full Stack Dev"** compound 配置一键启动。

### 功能页面

| 页面 | 功能 |
|------|------|
| **概览** | 收支卡片 + 月度柱状图 + 累计折线图 + 类别环形图(可点击) |
| **交易** | 多维筛选(类型/类别/账户/日期/标签) + 表格 + 分页 |
| **记一笔** | 模板选择 + 字段自动建议 + 子类别快速选择 + 标签选择器 |
| **预算** | 总览卡片 + 类别进度条 + 执行明细表 |
| **类别+标签** | 类别统计 + 标签管理(创建/颜色/删除) |
| **统计** | 9种分组 × 3种图表类型，点击图表跳转交易筛选 |

---

## 🐳 Docker 部署

镜像使用**多阶段构建**，自动编译 React 前端 + Python 后端，一个镜像搞定（不含 Node.js）。

### 拉取镜像

```bash
# Docker Hub（全球）
docker pull zouzhenglu/ledger:latest

# GitHub Container Registry（推荐开发者使用）
docker pull ghcr.io/kdeerfish/ledger:latest

# 阿里云（国内最快）
docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest
```

### 一键启动

```bash
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v /path/to/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger:latest
```

### 使用 docker-compose（推荐）

```bash
wget https://raw.githubusercontent.com/kdeerfish/ledger/master/docker-compose.yml
docker compose up -d
docker compose logs -f
```

> 数据库持久化在 `./data/ledger.db`，删容器不丢数据。

---

## 📖 CLI 命令速查

### 交易管理

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py add ...` | 添加一笔交易 |
| `python scripts/cli.py list` | 列出最近交易 |
| `python scripts/cli.py update --id 1 --field amount --value 50` | 修改交易 |
| `python scripts/cli.py delete --id 1` | 软删除（可恢复） |
| `python scripts/cli.py restore --id 1` | 恢复已删除 |
| `python scripts/cli.py hard_delete --id 1 --confirm` | 物理删除（不可恢复） |

### 搜索与筛选

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py search --keyword 午餐` | 全局搜索 |
| `python scripts/cli.py search --keyword 午餐 --search_type note` | 按备注搜索 |
| `python scripts/cli.py filter --category 食品` | 按类别筛选 |
| `python scripts/cli.py filter --account 微信 --start_date 2026-01-01` | 按账户+日期筛选 |

### 统计分析

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py summary` | 收支汇总 |
| `python scripts/cli.py summary --year 2026 --month 7` | 指定月份汇总 |
| `python scripts/cli.py stats --group_by category` | 按类别统计 |
| `python scripts/cli.py stats --group_by month` | 按月统计 |
| `python scripts/cli.py accounts` | 列出所有账户 |
| `python scripts/cli.py categories` | 列出所有类别 |
| `python scripts/cli.py members` | 列出所有成员 |

### 预算管理

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py budget_set --category 食品 --amount 1000` | 设置预算 |
| `python scripts/cli.py budget_check` | 检查本月预算执行 |
| `python scripts/cli.py budget_template_create --template_name "月度餐饮" ...` | 创建预算模板 |
| `python scripts/cli.py budget_template_apply --template_id 1` | 应用预算模板 |
| `python scripts/cli.py budget_template_suggest` | 智能推荐预算模板 |

### 记账模板（一键记账）

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py template_create --template_name "通勤" ...` | 创建记账模板 |
| `python scripts/cli.py template_list` | 列出模板 |
| `python scripts/cli.py template_apply --template_id 1` | 应用模板（自动记账） |
| `python scripts/cli.py template_suggest` | 智能推荐记账模板 |

### 数据导入导出

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py import_csv --file data.csv` | 导入随手记 CSV |
| `python scripts/cli.py export --output report.csv` | 导出 CSV |
| `python scripts/cli.py export --output report.json --format json` | 导出 JSON |
| `python scripts/cli.py reconcile_guide` | 对账指南 |

### AI Agent 集成

```bash
# JSON 接口调用（picoclaw Agent 使用）
python ledger-skills/scripts/ledger_cli.py add '{"type":"支出","amount":25.5,"category":"食品","account":"微信"}'
python ledger-skills/scripts/ledger_cli.py list '{"limit":5}'
python ledger-skills/scripts/ledger_cli.py summary '{"year":2026,"month":7}'
```

---

## 🛠 开发

### 项目结构

```
ledger/
├── frontend/               # React + Vite 前端
│   ├── src/                # 组件 (5个页面 + 3个组件)
│   ├── package.json
│   └── vite.config.js      # API 代理配置
├── ledger_modules/         # Python 核心业务模块
│   ├── db.py               # SQLite 初始化/迁移/标签
│   ├── transactions.py     # 交易 CRUD
│   ├── budgets.py          # 预算
│   └── config.py           # 配置管理
├── web/
│   ├── app.py              # Flask API (v2 全量)
│   └── run.py              # 启动脚本
├── tests/                  # 252 项 pytest 测试
├── .github/workflows/      # CI/CD: 测试 + 前端构建 + Docker
└── website/                # Docusaurus 文档站
```

### 常用 Make 命令

| 命令 | 说明 |
|------|------|
| `make test` | 运行 252 项测试 |
| `make coverage` | 测试 + 覆盖率报告 |
| `make lint` | ruff 代码检查 |
| `make deploy` | 构建前端 + 打包发布 |
| `make release` | 打包 + git tag + 发布 |

### 测试

```bash
# 全部测试
python -m pytest tests -v --tb=short

# 仅新功能测试（标签/模板/自动建议）
python -m pytest tests/test_new_features.py -v
```

---

## 📦 版本

当前版本 **v2.0.0** — 新增标签系统、React 前端、交互图表、自动建议、记账模板。

查看 [CHANGELOG](https://github.com/kdeerfish/ledger/releases) 了解完整变更历史。
