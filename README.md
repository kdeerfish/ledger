<div align="center">

# 📒 Ledger — 个人记账系统

**用自然语言记账，让 AI 帮你管钱**

[![Docker Pulls](https://img.shields.io/docker/pulls/zouzhenglu/ledger?logo=docker&label=Docker%20Hub)](https://hub.docker.com/r/zouzhenglu/ledger)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/kdeerfish/ledger/docker-publish.yml?branch=master&label=CI%2FCD&logo=github)](https://github.com/kdeerfish/ledger/actions)
[![License](https://img.shields.io/github/license/kdeerfish/ledger)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)

**🐳 [`docker`](https://hub.docker.com/r/zouzhenglu/ledger) · 📖 [完整文档](https://kdeerfish.github.io/ledger) · 🚀 [快速开始](docs/GETTING_STARTED.md)**

</div>

---

## ✨ 一句话介绍

> **用自然语言记账**，比如"京东买了200块零食"，AI 自动识别类别、账户、商家，帮你轻松管钱。

---

## 🚀 30 秒开始

```bash
# 1. 启动 Ledger
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data zouzhenglu/ledger:latest

# 2. 打开浏览器
# 访问 http://localhost:5800

# 3. 开始记账（对 AI 说）
"记一笔，买了杯咖啡15块"
```

**就这么简单！** 不需要学命令，不需要记参数，像跟朋友说话一样记账。

---

## 🎯 核心功能

### 📝 自然语言记账

```
"京东买了200块零食"           → 自动填写：类别=食品酒水，商家=京东
"今天打车花了20"              → 自动填写：类别=交通，账户=微信零钱
"收到工资5000到招商银行"       → 自动填写：类型=收入，账户=招商银行
```

### 📊 智能分析

```
"看看这个月花了多少"           → 显示本月收支汇总
"各个类别的支出占比"           → 显示类别统计图表
"在拼多多买了什么"             → 搜索商家记录
```

### 💰 预算管理

```
"设置本月食品预算2000"         → 创建预算
"预算还剩多少"                 → 显示预算执行情况
```

### 📥 数据导入导出

```
"导入随手记的CSV"              → 一键导入历史数据
"导出6月份的记录"              → 导出 CSV/JSON
```

---

## 📖 新手指南

**第一次使用？** 请阅读 **[新手完全指南](docs/GETTING_STARTED.md)**，包含：

1. ✅ 安装 Ledger（3种方式）
2. ✅ 导入历史数据
3. ✅ 让 AI 学习你的习惯
4. ✅ 日常记账技巧
5. ✅ 查看账单和统计
6. ✅ 预算管理
7. ✅ 常见问题解答

---

## 🏠 安装方式

| 方式 | 适用场景 | 命令 |
|------|----------|------|
| **Docker** | NAS、服务器 | `docker run -d -p 5800:5800 -v $(pwd)/data:/data zouzhenglu/ledger` |
| **Windows 桌面版** | Windows 用户 | [下载 Ledger.zip](https://github.com/kdeerfish/ledger/releases) 解压双击 |
| **源码** | 开发者 | `git clone` → `pip install -e .` → `python web/run.py` |

**国内镜像**：
```bash
docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest
```

---

## 🤖 AI Agent 集成

Ledger 支持与 AI Agent 集成，让 AI 帮你记账：

### 快速集成

1. **安装 Ledger 并启动**
2. **告诉 AI 你的 Ledger 地址**：`http://localhost:5800`
3. **说"学习"**：让 AI 分析你的历史数据
4. **开始用自然语言记账**

### 支持的 AI 平台

- ✅ Claude
- ✅ ChatGPT
- ✅ 其他支持 MCP 的 AI

### 详细文档

- [AI Agent 集成指南](website/docs/ai-agent/index.md)
- [技能包下载](https://github.com/kdeerfish/ledger/releases)

---

## 📚 文档导航

| 你想做什么？ | 看这里 |
|-------------|--------|
| **第一次安装**，不知道选什么方式 | 👉 [新手完全指南](docs/GETTING_STARTED.md) |
| 怎么用 **Web 界面** 记账 | 👉 [Web 界面使用手册](website/docs/user-guide/web-ui.md) |
| 怎么用 **命令行** 记账 | 👉 [CLI 命令参考](website/docs/user-guide/cli.md) |
| 想让 **AI Agent** 接管记账 | 👉 [AI Agent 集成指南](website/docs/ai-agent/index.md) |
| 数据库在哪 / 怎么备份 / 怎么迁移 | 👉 [FAQ · 数据管理](website/docs/faq/data.md) |
| 出问题了 | 👉 [FAQ · 常见问题](website/docs/faq/troubleshooting.md) |

**完整文档站**：[kdeerfish.github.io/ledger](https://kdeerfish.github.io/ledger)

---

## 🎬 使用场景示例

### 场景 1：买早餐

**你说**：
```
记一笔，早餐花了15块
```

**AI 自动记录**：
```json
{
  "type": "支出",
  "amount": 15,
  "category": "食品酒水",
  "subcategory": "早餐",
  "account": "微信零钱",
  "merchant": ""
}
```

### 场景 2：查看本月支出

**你说**：
```
看看这个月花了多少
```

**AI 返回**：
```
📊 6月收支汇总
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 总收入：¥15,000.00
💸 总支出：¥8,234.50
📊 结余：¥6,765.50
📅 日均支出：¥274.48
```

### 场景 3：导入历史数据

**你说**：
```
导入随手记的数据
```

**AI 指导你**：
```
请把 CSV 文件放到 data 目录，然后告诉我文件路径。
```

**你说**：
```
data/mymoney_data.csv
```

**AI 执行导入**：
```
✅ 导入完成，共 1528 笔记录
建议说"学习"让我分析你的记账习惯。
```

**你说**：
```
学习
```

**AI 分析完成**：
```
✅ 已学习完成！以后记账时我会自动参考这些习惯。
```

---

## 🌟 项目特点

| 特点 | 说明 |
|------|------|
| 🤖 **AI 驱动** | 自然语言记账，自动识别类别、账户、商家 |
| 🔒 **数据安全** | 数据存在你自己的设备，不上传到任何服务器 |
| 📱 **多端支持** | 手机、平板、电脑、NAS 都能用 |
| 🐳 **一键部署** | Docker 一键启动，无需复杂配置 |
| 📊 **智能分析** | 自动统计、预算提醒、趋势分析 |
| 🔄 **数据迁移** | 支持导入随手记、MoneyWiz 等软件的数据 |

---

## 🐳 Docker 镜像仓库

| 仓库 | 拉取命令 | 速度 |
|------|----------|------|
| **Docker Hub**（主） | `docker pull zouzhenglu/ledger:latest` | 🌍 全球 |
| GitHub Container Registry | `docker pull ghcr.io/kdeerfish/ledger:latest` | 🌍 备选 |
| **阿里云** | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` | 🇨🇳 国内最快 |

---

## 🛠️ 项目信息

| 项目 | 链接 |
|------|------|
| GitHub 仓库 | [kdeerfish/ledger](https://github.com/kdeerfish/ledger) |
| 完整文档站 | [kdeerfish.github.io/ledger](https://kdeerfish.github.io/ledger) |
| 问题反馈 | [Issues](https://github.com/kdeerfish/ledger/issues) |
| Docker Hub | [zouzhenglu/ledger](https://hub.docker.com/r/zouzhenglu/ledger) |
| 许可 | MIT |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**⭐ 如果觉得有用，请给个 Star 支持一下！⭐**

</div>
