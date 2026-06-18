# 🛠 开发指南

## 环境要求

- Python 3.10+
- Git
- Docker（可选，用于容器化部署）

---

## 搭建开发环境

```bash
# 克隆项目
git clone https://github.com/kdeerfish/ledger.git
cd ledger

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e ".[dev,lint]"

# 验证安装
python scripts/cli.py --help
```

## 项目结构

```
ledger/
├── ledger_modules/          # 核心业务模块
│   ├── __init__.py          # 统一导出
│   ├── db.py                # SQLite 数据库初始化/迁移
│   ├── transactions.py      # 交易 CRUD / 搜索 / 筛选 / 导出 / 统计
│   ├── budgets.py           # 预算 / 多维度预算 / 模板
│   └── config.py            # 配置管理（.env 加载）
├── scripts/
│   ├── cli.py               # CLI 入口
│   ├── import_ledger.py     # CSV 导入
│   ├── release.py           # 自动发布脚本
│   └── deploy.py            # 打包发布脚本
├── web/                     # Flask Web 界面
│   ├── app.py               # 后端 API
│   ├── run.py               # 启动脚本
│   ├── templates/           # HTML 模板
│   └── static/              # CSS 样式
├── tests/                   # pytest 测试
│   ├── conftest.py          # 共享 fixture
│   ├── test_db.py           # 数据库测试
│   ├── test_transactions.py # 交易测试
│   ├── test_budgets.py      # 预算测试
│   ├── test_robustness.py   # 健壮性测试
│   └── test_integration.py  # 集成测试
├── skills/                  # AI Agent 技能
├── .github/workflows/       # GitHub Actions CI/CD
└── docs/                    # 文档
```

---

## 开发流程

### 1. 创建 Feature 分支

```bash
git checkout -b feat/my-feature
```

### 2. 实现功能

业务逻辑放 `ledger_modules/`，CLI 入口放 `scripts/cli.py`，Web API 放 `web/app.py`。

**原则：** CLI 只负责参数解析，所有逻辑委托给 `ledger_modules/`。

### 3. 编写测试

```bash
# 在 tests/ 下添加测试文件
# 运行测试
python -m pytest tests -v --tb=short
```

### 4. 代码检查

```bash
make lint       # ruff 检查
make lint-fix   # 自动修复
make format     # 格式化
```

### 5. 提交

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

---

## 运行测试

```bash
# 全部测试
make test

# 快速模式
make test-quick

# 匹配测试名
python -m pytest tests -v -k "test_budget"

# 覆盖率
make coverage
# 或
python -m pytest tests --cov=ledger_modules --cov=scripts --cov-report=term --cov-report=html
```

当前测试覆盖：**86%**（102+ 测试用例）

---

## 常用 Make 命令

| 命令 | 说明 |
|------|------|
| `make test` | 运行测试 |
| `make coverage` | 测试 + 覆盖率报告 |
| `make lint` | ruff 代码检查 |
| `make lint-fix` | 自动修复 |
| `make format` | 格式化代码 |
| `make clean` | 清理缓存 |
| `make install` | 安装开发依赖 |
| `make deploy` | 打包发布到 deploy/ |
| `make release` | 打包 + git tag + 发布 |

---

## 数据库

Ledger 使用 SQLite 数据库，自动创建和迁移。

**表结构：**

```sql
-- 交易记录
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,           -- 支出 / 收入
    amount REAL NOT NULL,
    category TEXT, subcategory TEXT,
    account TEXT, project TEXT, member TEXT, merchant TEXT,
    note TEXT,
    trans_date TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0  -- 软删除标记
);

-- 预算
CREATE TABLE budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT, year INTEGER, month INTEGER, amount REAL,
    dimension_type TEXT DEFAULT 'category',
    dimension_value TEXT,
    UNIQUE(category, year, month, dimension_type, dimension_value)
);

-- 预算模板
CREATE TABLE budget_templates (...);

-- 记录模板
CREATE TABLE record_templates (...);
```

---

## CI/CD

项目使用 GitHub Actions 自动构建和发布：

1. Push master → 运行测试 → 构建 Docker → 推送到 3 个仓库
2. Push tag v* → 同上 + 版本标签

配置见 [`.github/workflows/docker-publish.yml`](https://github.com/kdeerfish/ledger/blob/master/.github/workflows/docker-publish.yml)。

---

## 发布新版本

```bash
# 自动发布（交互式）
python scripts/release.py

# 发布指定版本
python scripts/release.py 1.6.0

# 只打包，不发布
python scripts/release.py --dry-run
```

---

## 文档

文档在 `docs/` 目录下，使用 Markdown 编写，GitHub Pages 自动渲染。

```bash
# 本地预览文档
# 安装 jekyll 后
cd docs
jekyll serve
```
