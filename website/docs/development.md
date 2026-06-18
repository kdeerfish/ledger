---
sidebar_position: 15
---

# 🛠 开发指南

## 环境要求

- Python 3.10+
- Node.js 20+（仅前端开发时需要）
- Git
- Docker（可选，用于容器化部署）

## 搭建开发环境

```bash
# 克隆项目
git clone https://github.com/kdeerfish/ledger.git
cd ledger

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装 Python 开发依赖
pip install -e ".[dev,lint]"

# 安装前端依赖（可选，仅开发 Web 界面时需要）
cd frontend && npm install && cd ..

# 验证安装
python scripts/cli.py --help
```

## 项目结构

```
ledger/
├── frontend/                   # React + Vite 前端
│   ├── src/
│   │   ├── api/index.js        # API 客户端
│   │   ├── components/         # 共享组件（Layout/TagSelector/TransactionForm）
│   │   ├── pages/              # 5 个页面（Dashboard/Transactions/Budgets/Categories/Stats）
│   │   ├── App.jsx             # 路由入口
│   │   └── App.css             # 响应式样式
│   ├── package.json
│   └── vite.config.js          # API 代理 + 构建配置
├── ledger_modules/             # Python 核心业务模块
│   ├── __init__.py
│   ├── db.py                   # SQLite 初始化/迁移/标签辅助函数
│   ├── transactions.py         # 交易 CRUD / 搜索 / 筛选 / 导出 / 统计
│   ├── budgets.py              # 预算 / 多维度预算 / 模板
│   └── config.py               # 配置管理（.env 加载）
├── scripts/
│   ├── cli.py                  # CLI 入口
│   ├── import_ledger.py        # CSV 导入
│   ├── release.py              # 自动发布脚本
│   └── deploy.py               # 打包发布脚本（含前端构建）
├── web/                        # Flask 后端 API
│   ├── app.py                  # API v2（含 Tags/Templates/增强统计/自动建议）
│   └── run.py                  # 启动脚本
├── tests/                      # 252 项 pytest 测试
│   ├── test_api_integration.py # API 集成测试（42 项）
│   ├── test_new_features.py    # 新增功能测试：Tags/Templates/Suggestions/增强统计（23 项）
│   ├── test_budgets.py         # 预算测试
│   ├── test_db.py              # 数据库测试
│   ├── test_transactions.py    # 交易测试
│   ├── test_robustness.py      # 健壮性测试
│   ├── test_integration.py     # 集成测试
│   └── ...
├── skills/                     # AI Agent 技能
├── .github/workflows/          # GitHub Actions CI/CD
└── website/                    # Docusaurus 文档站
```

## 开发流程

### 1. 创建 Feature 分支

```bash
git checkout -b feat/my-feature
```

### 2. 实现功能

业务逻辑放 `ledger_modules/`，CLI 入口放 `scripts/cli.py`，Web API 放 `web/app.py`，前端放 `frontend/src/`。

**原则：** CLI 只负责参数解析，所有逻辑委托给 `ledger_modules/`。API 和前端通过 JSON 通信。

### 3. 编写测试

```bash
# 在 tests/ 下添加测试文件
# 运行测试
python -m pytest tests -v --tb=short
```

### 4. 前端开发（需要热更新）

```bash
# 终端 1: Flask 后端
WEB_DEBUG=true python web/run.py

# 终端 2: Vite 开发服务器
cd frontend && npm run dev

# 访问 http://localhost:5800 — Flask 自动代理到 Vite，代码改完即刷新
```

### 5. 代码检查

```bash
make lint       # ruff 检查
make lint-fix   # 自动修复
make format     # 格式化
```

### 6. 提交

```bash
git add .
git commit -m "feat: 添加xxx功能"

# 提交信息格式：
# feat: 新功能
# fix: 修复
# refactor: 重构
# test: 测试
# docs: 文档
# chore: 杂项
```

## 运行测试

```bash
# 全部 252 项测试
make test

# 快速模式
make test-quick

# 匹配测试名
python -m pytest tests -v -k "test_tag"

# 新功能测试
python -m pytest tests/test_new_features.py -v

# 覆盖率
make coverage
# 或
python -m pytest tests --cov=ledger_modules --cov=scripts --cov-report=term --cov-report=html
```

当前测试覆盖：**86%**（252 测试用例）

## 常用 Make 命令

| 命令 | 说明 |
|------|------|
| `make test` | 运行 252 项测试 |
| `make coverage` | 测试 + 覆盖率报告 |
| `make lint` | ruff 代码检查 |
| `make lint-fix` | 自动修复 |
| `make format` | 格式化代码 |
| `make clean` | 清理缓存 |
| `make install` | 安装开发依赖 |
| `make deploy` | 构建前端 + 打包发布到 deploy/ |
| `make release` | 打包 + git tag + 发布 |

## 数据库

Ledger 使用 SQLite 数据库，自动创建和迁移（版本 v2）。

**表结构（v2）：**

```sql
-- 交易记录
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,           -- 支出 / 收入
    amount REAL NOT NULL,
    category TEXT, subcategory TEXT,
    account TEXT, project TEXT, member TEXT, merchant TEXT,
    note TEXT, trans_date TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0  -- 软删除标记
);
CREATE INDEX idx_trans_date ON transactions(trans_date);
CREATE INDEX idx_trans_category ON transactions(category);
CREATE INDEX idx_trans_type ON transactions(type);

-- 预算
CREATE TABLE budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT, year INTEGER, month INTEGER, amount REAL,
    dimension_type TEXT DEFAULT 'category',
    dimension_value TEXT,
    UNIQUE(category, year, month, dimension_type, dimension_value)
);

-- 标签
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#6366f1',
    created_at TEXT NOT NULL
);

-- 交易-标签关联（多对多）
CREATE TABLE transaction_tags (
    transaction_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (transaction_id, tag_id),
    FOREIGN KEY (transaction_id) REFERENCES transactions(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- 记账模板
CREATE TABLE record_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, type TEXT, amount REAL DEFAULT 0,
    category TEXT, subcategory TEXT, account TEXT,
    project TEXT, member TEXT, merchant TEXT, note TEXT,
    tags TEXT DEFAULT '',  -- 逗号分隔的标签名
    usage_count INTEGER DEFAULT 0,
    last_used_at TEXT, created_at TEXT NOT NULL
);
```

## CI/CD

项目使用 GitHub Actions 自动构建和发布：

```mermaid
graph LR
    A[Push master/tag] --> B[Run Tests (252)]
    B --> C[Build Frontend (npm)]
    C --> D[Build Docker]
    D --> E[Docker Hub]
    D --> F[ghcr.io]
    D --> G[阿里云]
```

1. Push master → 运行 252 项测试 → `npm run build` → 构建 Docker → 推送到 3 个仓库
2. Push tag v* → 同上 + 版本标签

配置见 [`.github/workflows/docker-publish.yml`](https://github.com/kdeerfish/ledger/blob/master/.github/workflows/docker-publish.yml)。

## 发布新版本

```bash
# 自动发布（交互式）
python scripts/release.py

# 发布指定版本
python scripts/release.py 2.0.0

# 只打包，不发布
python scripts/release.py --dry-run
```
