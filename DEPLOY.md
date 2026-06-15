# Ledger 部署指南

## 📦 部署包说明

| 包 | 说明 |
|----|------|
| `ledger-service.zip` | 核心服务（ledger_modules + scripts） |
| `ledger-skills.zip` | picoclaw / AI Agent 技能 |

---

## 🚀 本地测试

### 1. 部署服务端

```bash
# 解压服务端
unzip ledger-service.zip -d /path/to/ledger
cd /path/to/ledger

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 设置 LEDGER_PATH 和 LEDGER_DB_PATH

# 导入数据（如果有 CSV）
python scripts/import_ledger.py data.csv

# 测试运行
python scripts/cli.py list
python scripts/cli.py summary --year 2026 --month 7
```

### 2. 部署 Skills

```bash
# 解压 Skills
unzip ledger-skills.zip -d ~/.picoclaw/skills/ledger

# 配置服务路径
cd ~/.picoclaw/skills/ledger
cp .env.example .env
# 编辑 .env 设置 LEDGER_PATH 指向服务目录
```

### 3. 测试 Skills 调用

```bash
# 测试添加
python ~/.picoclaw/skills/ledger/scripts/ledger_cli.py add '{"type":"expense","amount":25.5,"category":"食品酒水","account":"微信","note":"测试"}'

# 测试查询
python ~/.picoclaw/skills/ledger/scripts/ledger_cli.py list '{"limit":5}'
```

---

## 🐳 NAS 部署

### 1. 上传文件

```bash
# 上传到 NAS
scp ledger-service.zip user@nas:/volume1/docker/ledger/
scp ledger-skills.zip user@nas:/volume1/docker/ledger/
```

### 2. 在 NAS 上部署

```bash
# SSH 到 NAS
ssh user@nas

# 解压服务端
cd /volume1/docker/ledger
unzip ledger-service.zip

# 配置环境变量
cp .env.example .env
cat > .env << EOF
LEDGER_PATH=/volume1/docker/ledger
LEDGER_DB_PATH=/volume1/docker/ledger/ledger.db
EOF

# 导入数据
python scripts/import_ledger.py data.csv

# 验证
python scripts/cli.py list
```

### 3. 部署 Skills

```bash
# 解压 Skills
unzip ledger-skills.zip -d ~/.picoclaw/skills/ledger

# 配置服务路径
cd ~/.picoclaw/skills/ledger
cp .env.example .env
cat > .env << EOF
LEDGER_PATH=/volume1/docker/ledger
EOF
```

---

## 📁 部署后的目录结构

```
/volume1/docker/ledger/
├── .env                    # 服务配置
├── ledger_modules/
├── scripts/
└── ledger.db

~/.picoclaw/skills/ledger/
├── .env                    # 指向服务路径
├── SKILL.md
└── scripts/
    └── ledger_cli.py
```

---

## 🔧 常用命令

```bash
# 测试服务端
python scripts/cli.py list
python scripts/cli.py summary --year 2026 --month 7
python scripts/cli.py budget_check

# 测试 Skills
python ~/.picoclaw/skills/ledger/scripts/ledger_cli.py list '{"limit":10}'

# 重新导入数据
python scripts/import_ledger.py data.csv
```

---

## ❓ 故障排除

### 问题：找不到 cli.py

**原因：** LEDGER_PATH 未正确设置

**解决：**
```bash
# 检查当前配置
echo $LEDGER_PATH

# 重新设置
export LEDGER_PATH=/volume1/docker/ledger
```

### 问题：数据库不存在

**原因：** 首次运行需要初始化

**解决：**
```bash
# 导入数据会自动创建数据库
python scripts/import_ledger.py data.csv
```
