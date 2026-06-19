---
name: ledger
description: 记账、查账、统计、预算、导入导出、学习用户习惯等个人财务管理工具（HTTP API 版）
version: 2.1.0
---

# Ledger - 个人记账系统

## 系统架构

```
AI Agent ──HTTP──→ Docker 容器
    │                   │
    │   ledger_cli.py   │  Web UI (Flask)
    │   (API 客户端)    │  REST API
    │                   │  SQLite Database
    └───────────────────┘
```

- Agent **不再直接读写 SQLite**，全部通过 HTTP API 操作
- Ledger 运行在 Docker 容器中，数据持久化在宿主机
- Agent 可运行在**任何位置**（同机、远端、另一台 NAS）

## 配置

在 `skills/ledger/.env` 中配置 API 地址：

```bash
LEDGER_API_URL=http://127.0.0.1:5800
```

### 场景配置

| 部署方式 | .env 配置 | 说明 |
|----------|-----------|------|
| **Docker 在本机** | `http://127.0.0.1:5800` | 默认值，无需配置 |
| **Docker 在 NAS 上，本机访问** | `http://<NAS-IP>:5800` | 如 `http://192.168.31.126:5800` |
| **Docker 在 WSL 同机** | 无需配置 | 自动探测网关 IP |
| **Docker 在 Windows 宿主机，WSL 访问** | 无需配置 | 自动探测 WSL 网关 |

> `ledger_cli.py` 内置自动探测：配置的地址不通时，会依次尝试 `127.0.0.1` → WSL 网关 → 配置值。
> 部署到 NAS 后，电脑上的 agent 只需在 `.env` 填 NAS 的局域网 IP 即可。

## 部署与安装

### 一、服务端（Docker）

在飞牛 NAS 或任意机器上部署 Ledger Docker 容器，端口 `5800`。

```bash
# 飞牛 NAS 示例
docker pull ledger-web:latest
docker run -d -p 5800:5800 -v /vol1/ledger-data:/app/data ledger-web
```

验证服务已启动：
```bash
curl http://<NAS-IP>:5800/api/health
```

### 二、Agent 端（Skills 安装）

#### 场景 A：NAS 本机 agent

直接把 `skills/ledger/` 放到 agent 的技能目录，**不需要配置 `.env`**，默认连 `127.0.0.1:5800`。

#### 场景 B：Windows 电脑 agent

1. 复制 `skills/ledger/` 到 agent 技能目录（如 `~/.agents/skills/ledger/`）
2. 在 `skills/ledger/` 下创建 `.env` 文件，写入 NAS 地址：
   ```
   LEDGER_API_URL=http://192.168.31.126:5800
   ```
3. 完成。所有 Windows 上的 agent 共用这一份配置。

#### 场景 C：WSL hermes

1. WSL 读取 Windows 上的 `~/.agents/skills/ledger/`（通过 `/mnt/c/` 访问）
2. 同一个 `.env` 文件，**不用额外配置**
3. 或者在 `~/.hermes/config.yaml` 中添加：
   ```yaml
   skills:
     external_dirs:
       - /mnt/c/Users/<用户名>/.agents/skills
   ```

### 三、验证连接

```bash
python3 scripts/ledger_cli.py health '{}'
```

返回 `"success": true` 即表示连接正常。

## 核心概念

通过 `python3 scripts/ledger_cli.py <command> '<json_args>'` 调用，所有命令返回 JSON 格式。

### 常用命令

```bash
# 记账
python3 scripts/ledger_cli.py add '{"type":"支出","amount":30,"category":"食品酒水","account":"微信零钱"}'

# 查账
python3 scripts/ledger_cli.py list '{"limit":10}'

# 统计
python3 scripts/ledger_cli.py summary '{"year":2026,"month":6}'

# 分析数据
python3 scripts/ledger_cli.py analyze '{}'

# 检查 API 连接
python3 scripts/ledger_cli.py health '{}'
```

## 文档索引

详细文档位于 `references/` 目录：

| 文档 | 内容 | 何时读取 |
|------|------|----------|
| `references/basic.md` | 基础命令 (add/list/search/filter/summary/stats) | 记账、查账、搜索时 |
| `references/modify.md` | 修改命令 (update/delete/restore) | 修改、删除记录时 |
| `references/budget.md` | 预算命令 (budget_set/budget_check) | 设置、查看预算时 |
| `references/template.md` | 通用记录模板 (template_*) | 使用模板快速记账时 |
| `references/data.md` | 数据命令 (export/analyze) | 导出、分析数据时 |
| `references/field-guide.md` | 字段用途说明、场景示例 | 不确定字段怎么填时 |

> 每个参考文档都有对应的日常操作示例，见 `examples/` 目录。

## 工作流程

### 流程 1：首次使用 / 学习习惯

当用户说"学习"、"学习我的习惯"、"分析我的数据"时：

1. **调用 analyze 命令**：
   ```bash
   python3 scripts/ledger_cli.py analyze '{}'
   ```

2. **阅读分析报告**，重点关注：
   - 【账户】列表（付款方式/资金来源）
   - 【商家】列表（消费场所/平台）
   - 【类别→子类别】（消费分类习惯）
   - 【成员】列表（家庭成员）
   - 【项目】列表（长期项目）

3. **用 remember 工具保存关键模式**到记忆

### 流程 2：日常记账

```
用户："今天花了30块买零食"
→ 根据 field-guide 正确填写字段
→ 执行 add 命令
```

## 重要规则

### 去重检查

添加记录时自动检查相似记录。发现重复时需设置 `"force": true` 跳过检查。

### 输出格式

所有命令统一返回：
```json
{
  "success": true,
  "data": "..."
}
```

## 快速参考

### 预算管理

```bash
# 设置预算
python3 scripts/ledger_cli.py budget_set '{"category":"食品酒水","amount":2000}'

# 检查预算
python3 scripts/ledger_cli.py budget_check '{}'
```

### 数据统计

```bash
# 按类别统计
python3 scripts/ledger_cli.py stats '{"group_by":"category"}'

# 按账户统计
python3 scripts/ledger_cli.py stats '{"group_by":"account"}'

# 按月统计
python3 scripts/ledger_cli.py stats '{"group_by":"month"}'
```
