# 📒 Ledger 文档站

**Ledger** 是一个个人记账系统，支持 CLI 命令行、Web 界面、AI Agent 集成，可通过 Docker 一键部署。

---

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } __一分钟上手__

    ---

    ```bash
    pip install -e ".[dev,lint]"
    python scripts/cli.py add --type 支出 --amount 100 --category 食品 --account 微信
    python scripts/cli.py list
    python scripts/cli.py summary
    ```

    [:octicons-arrow-right-24: CLI 命令参考](cli.md)

-   :fontawesome-brands-docker:{ .lg .middle } __Docker 部署__

    ---

    ```bash
    docker pull zouzhenglu/ledger:latest
    docker run -d --name ledger -p 5800:5800 -v ./data:/data zouzhenglu/ledger:latest
    ```

    [:octicons-arrow-right-24: Docker 指南](docker.md)

-   :material-api:{ .lg .middle } __Web 界面 & API__

    ---

    基于 Flask + Bootstrap 5 的响应式管理界面，提供 RESTful JSON API，支持交易管理、预算仪表盘、统计图表。

    [:octicons-arrow-right-24: Web 界面](web.md) · [:octicons-arrow-right-24: API 文档](api.md)

-   :material-code-tags:{ .lg .middle } __开发 & 贡献__

    ---

    Python 3.10+，SQLite 持久化，pytest 测试覆盖率 86%，GitHub Actions CI/CD 自动构建 Docker 镜像。

    [:octicons-arrow-right-24: 开发指南](development.md)

</div>

---

## ✨ 功能总览

=== "📊 交易管理"

    | 功能 | 说明 |
    |------|------|
    | **记账** | 添加 / 编辑 / 软删除 / 恢复 / 物理删除 |
    | **搜索** | 关键词搜索（备注/类别/商家/全局） |
    | **筛选** | 按类别 / 账户 / 成员 / 日期范围 多条件筛选 |
    | **导入** | 随手记 CSV 一键导入，自动去重 |
    | **导出** | CSV / JSON 格式导出 |

=== "💰 预算管理"

    | 功能 | 说明 |
    |------|------|
    | **预算设置** | 按月 / 类别 / 账户 / 成员 / 项目 设置预算 |
    | **进度跟踪** | 实时计算已用额度，进度条展示，超支预警 |
    | **预算模板** | 创建 → 列表 → 更新 → 删除 → 一键应用 |
    | **智能推荐** | 基于历史记录自动推荐预算模板 |

=== "📈 统计分析"

    | 功能 | 说明 |
    |------|------|
    | **收支汇总** | 按年 / 月查看总收入、总支出、结余 |
    | **多维度统计** | 按类别 / 账户 / 月份分组聚合 |
    | **数据交叉分析** | 商家→类别、账户→商家 关联分析（供 AI Agent 学习） |
    | **成员统计** | 各成员收支统计 |

=== "🤖 AI Agent"

    | 功能 | 说明 |
    |------|------|
    | **JSON 接口** | 通过 `ledger_cli.py` 接收 JSON 参数 |
    | **技能包** | 为 [picoclaw](https://github.com/zouzhenglu/picoclaw) 提供技能文档 |
    | **数据学习** | `analyze` 命令输出结构化数据摘要供 Agent 学习用户习惯 |

=== "🌐 Web 界面"

    | 功能 | 说明 |
    |------|------|
    | **概览 Dashboard** | 收支汇总卡片 + 趋势图 + 最近交易 |
    | **交易管理** | 列表 / 搜索 / 筛选 / 新增 / 编辑 / 删除 |
    | **预算仪表盘** | 进度条 + 超支预警 |
    | **统计图表** | 按类别 / 账户 / 月份 分组展示 |

=== "🐳 Docker"

    | 功能 | 说明 |
    |------|------|
    | **三仓库推送** | Docker Hub + ghcr.io + 阿里云 |
    | **自动构建** | push master / tag v* 自动触发 |
    | **健康检查** | 内置 HEALTCHECK，每 30s 检测 |
    | **非 root 运行** | 安全加固，非 root 用户运行容器 |

---

## 🐳 快速部署

```bash
# 拉取镜像（选择最快的源）
# 国内用户推荐阿里云：
docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest

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

!!! tip "国内用户"
    阿里云镜像速度最快，无需代理：`crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger`

[:octicons-arrow-right-24: 完整 Docker 部署指南](docker.md)

---

## 📦 镜像仓库

| 仓库 | 拉取命令 | 速度 |
|------|----------|------|
| [Docker Hub](https://hub.docker.com/r/zouzhenglu/ledger) | `docker pull zouzhenglu/ledger:latest` | 🌍 全球 |
| [ghcr.io](https://github.com/kdeerfish/ledger/pkgs/container/ledger) | `docker pull ghcr.io/kdeerfish/ledger:latest` | 🌍 全球 |
| 阿里云容器镜像服务 | `docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest` | 🇨🇳 国内最快 |

---

## 📚 文档目录

<div class="grid cards" markdown>

-   :material-console-line: [__CLI 命令参考__](cli.md)
-   :material-web: [__Web 界面指南__](web.md)
-   :material-api: [__API 文档__](api.md)
-   :material-docker: [__Docker 部署__](docker.md)
-   :material-wrench: [__开发指南__](development.md)
-   :material-language-markdown: [__English Docs__](en/README.md)

</div>

---

## 🌟 项目信息

| 项目 | 链接 |
|------|------|
| GitHub 仓库 | [kdeerfish/ledger](https://github.com/kdeerfish/ledger) |
| 问题反馈 | [Issues](https://github.com/kdeerfish/ledger/issues) |
| Docker Hub | [zouzhenglu/ledger](https://hub.docker.com/r/zouzhenglu/ledger) |
| 许可 | MIT |
