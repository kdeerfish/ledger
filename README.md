# 📒 Ledger - 个人记账系统

支持收支管理、预算规划、多维度统计的 CLI 记账工具。

## 目录结构

```
ledger/
├── ledger_modules/          # 核心模块包
│   ├── __init__.py          # 统一导出
│   ├── config.py            # 配置管理（.env 加载）
│   ├── db.py                # 数据库初始化/迁移
│   ├── transactions.py      # 交易 CRUD / 搜索 / 筛选 / 导出 / 统计
│   └── budgets.py           # 预算 / 多维度预算 / 模板
├── scripts/                 # 命令行入口
│   ├── cli.py               # 统一的 CLI 入口（委托 ledger_modules）
│   └── import_ledger.py     # CSV 导入脚本
├── ledger-skills/           # picoclaw / AI Agent 技能
│   ├── SKILL.md             # 技能说明文档
│   └── scripts/
│       └── ledger_cli.py    # JSON 接口封装
├── tests/                   # 自动化测试（pytest）
│   ├── conftest.py          # 共享 fixture（自动管理临时 DB）
│   ├── test_db.py           # 数据库表结构测试
│   ├── test_transactions.py # 交易 CRUD / 搜索 / 筛选 / 导出 / 统计
│   ├── test_budgets.py      # 预算 / 多维度 / 模板 CRUD
│   ├── test_robustness.py   # 健壮性测试（边界条件、错误处理）
│   └── test_integration.py  # 端到端工作流 + CSV 导入
├── web/                     # Web 管理界面 (Flask)
│   ├── app.py               # Flask 后端 API
│   ├── run.py               # 一键启动脚本
│   ├── templates/           # HTML 模板
│   └── static/              # CSS 样式
├── data/
│   └── sample/              # 示例数据（随手记 CSV 导出）
├── .env.example             # 环境变量配置模板
├── pyproject.toml            # 项目配置 / pytest / coverage / ruff
├── Makefile                  # 常用命令快捷入口
├── .gitignore
├── .vscode/
│   └── launch.json
└── ledger.db                 # SQLite 数据库（运行时生成，已 gitignore）
```

## 快速开始

```bash
# 1. 安装开发依赖
pip install -e ".[dev,lint]"

# 2. 配置环境变量（可选，留空使用默认值）
cp .env.example .env
# 编辑 .env 设置 LEDGER_PATH 和 LEDGER_DB_PATH

# 3. 导入随手记 CSV
python scripts/import_ledger.py data/sample/mymoney_data.csv

# 4. 查看最近交易
python scripts/cli.py list

# 5. 添加一笔支出
python scripts/cli.py add --type expense --amount 100 --category 食品 --account 微信

# 6. 查看本月收支汇总
python scripts/cli.py summary --year 2026 --month 7

# 7. 设置预算
python scripts/cli.py budget_set --category 食品 --amount 1000 --year 2026 --month 7
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `python scripts/cli.py add ...` | 记一笔 |
| `python scripts/cli.py list` | 查看最近交易 |
| `python scripts/cli.py summary` | 收支汇总 |
| `python scripts/cli.py search --keyword xxx` | 搜索 |
| `python scripts/cli.py filter --category 食品` | 筛选 |
| `python scripts/cli.py update --id 1 --field amount --value 50` | 修改 |
| `python scripts/cli.py delete --id 1` | 软删除 |
| `python scripts/cli.py restore --id 1` | 恢复 |
| `python scripts/cli.py budget_set ...` | 设置预算 |
| `python scripts/cli.py budget_check` | 检查预算 |
| `python scripts/cli.py budget_template_create ...` | 创建预算模板 |
| `python scripts/cli.py export --output report.csv` | 导出 |
| `python scripts/cli.py stats` | 统计分析 |

## 测试

```bash
# 运行所有测试（102 个测试，覆盖率 86%）
make test

# 运行特定测试
python -m pytest tests -v -k "test_budget"

# 查看覆盖率
make coverage

# 打开 HTML 覆盖率报告
make coverage-view
```

## 开发

```bash
# 代码检查
make lint

# 自动修复
make lint-fix

# 格式检查
make format

# 清理缓存
make clean
```

## 环境变量配置

通过 `.env` 文件配置，优先级：系统环境变量 > `.env` 文件 > 默认值

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
LEDGER_PATH=/path/to/ledger      # 项目根目录（默认：当前目录）
LEDGER_DB_PATH=/path/to/ledger.db  # 数据库路径（默认：./ledger.db）
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LEDGER_PATH` | ledger 项目根目录 | 当前目录 |
| `LEDGER_DB_PATH` | SQLite 数据库路径 | `./ledger.db` |

## picoclaw / AI Agent 集成

```bash
# 通过 ledger-skills/scripts/ledger_cli.py 调用
python ledger-skills/scripts/ledger_cli.py add '{"type":"expense","amount":25.5,"category":"食品酒水","account":"微信","note":"零食"}'
python ledger-skills/scripts/ledger_cli.py list '{"limit":5}'
python ledger-skills/scripts/ledger_cli.py summary '{"year":2026,"month":7}'
```

## 技术栈

- Python 3.10+
- SQLite 持久化
- Flask Web 框架（可选，用于 Web 界面）
- pytest / pytest-cov 测试
- ruff 代码检查

---

## Web 管理界面

Ledger 提供一个开箱即用的 Web 管理界面，适配飞牛OS (FnOS) 及任何 Linux 环境。

### 快速启动

```bash
# 1. 安装依赖
pip install flask flask-cors

# 2. 启动服务
python web/run.py

# 3. 打开浏览器
# 本地访问: http://127.0.0.1:5000
# NAS访问:  http://NAS_IP:5000
```

### 功能一览

| 页面 | 功能 |
|------|------|
| **概览** | 收支汇总卡片、月度趋势图、最近交易 |
| **交易** | 全部交易列表、搜索/筛选、新增/编辑/删除（软删除可恢复） |
| **预算** | 按类别/月设置预算、实时进度跟踪、超支预警 |
| **类别** | 类别/子类别层级展示、消费金额统计 |
| **统计** | 按类别/账户/月份分组统计、图表展示 |

### 🐳 Docker 部署（推荐）

这是最省心的方式，飞牛OS Docker 界面点几下就行。

#### 方式一：飞牛OS Docker 界面（最简单）

```bash
# 1. SSH 到飞牛OS，创建项目目录
ssh admin@nas_ip
mkdir -p /volume1/docker/ledger/data
cd /volume1/docker/ledger

# 2. 下载 docker-compose.yml
wget -O docker-compose.yml https://raw.githubusercontent.com/zouzhenglu/ledger/refactor-docker/docker-compose.yml

# 3. 在飞牛OS Docker 界面 → 项目 → 新建
#    - 选择 /volume1/docker/ledger 目录
#    - 点击部署，稍等片刻
#    - 访问 http://飞牛OS_IP:5000
```

#### 方式二：命令行直接跑

```bash
# 构建镜像
docker compose build

# 或者从源码构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down

# 升级（拉取新代码后）
git pull
docker compose up -d --build
```

#### 方式三：使用预构建镜像（开发中）

```bash
docker run -d \
  --name ledger \
  -p 5000:5000 \
  -v /path/to/data:/data \
  --restart unless-stopped \
  ledger:latest
```

#### 数据持久化

数据库保存在 `./data/ledger.db`，删容器不会丢数据。
如需导入老数据，把 `ledger.db` 复制到 `./data/` 目录下，重启容器即可。

---

### 传统方式部署（无 Docker）

```bash
# 1. 安装依赖
pip install flask flask-cors

# 2. 启动
python web/run.py

# 3. 访问 http://127.0.0.1:5000

# 后台运行
nohup python web/run.py > ledger-web.log 2>&1 &

# 查看日志
tail -f ledger-web.log

kill $(pgrep -f "web/run.py")
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WEB_HOST` | 监听地址 | `0.0.0.0` |
| `WEB_PORT` | 监听端口 | `5000` |
| `WEB_DEBUG` | 调试模式 | `false` |

### 截图预览

Web 界面使用 Bootstrap 5 响应式设计，在手机、平板、电脑上均可正常使用。
包含：Dashboard 概览看板、收支趋势图、交易记录表格、预算进度条等。`
