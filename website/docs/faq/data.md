---
sidebar_position: 8
---

# 💾 数据管理

数据库是 SQLite 文件，**整个 Ledger 就是一个 `.db` 文件**——备份、迁移、跨平台，全靠它。

---

## 📍 数据库在哪里？

### Docker 部署

| 启动方式 | 实际位置 |
|---------|---------|
| `docker run -v ./data:/data ...` | `./data/ledger.db`（宿主机当前目录） |
| `docker compose`（项目根目录执行） | `./data/ledger.db`（compose 文件所在目录） |
| 未挂载卷 | Docker 匿名卷，**容器删了数据可能没** |

### 源码运行

| 配置 | 路径 |
|------|------|
| 默认 | 项目根目录的 `./ledger.db` |
| `.env` 里 `LEDGER_DB_PATH=...` | 自定义路径 |

---

## ✅ 怎么确认数据持久化没丢？

```bash
# 检查容器是否有挂载卷
docker inspect ledger --format '{{json .Mounts}}'
```

应该看到类似：

```json
[{"Type":"bind","Source":"/your/path/data","Destination":"/data","Mode":"","RW":true,...}]
```

如果 `Source` 是 `/var/lib/docker/volumes/...` 这种路径，是**匿名卷**，建议改成显式挂载：

```bash
# 1. 先停容器
docker stop ledger

# 2. 备份数据（从匿名卷复制出来）
docker cp ledger:/data/ledger.db ./ledger-backup.db

# 3. 删容器 + 匿名卷
docker rm ledger
docker volume prune   # 警告：会删所有未用匿名卷，看清楚

# 4. 重新启动，用显式挂载
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data --restart unless-stopped zouzhenglu/ledger:latest

# 5. 恢复数据
cp ./ledger-backup.db ./data/ledger.db
docker restart ledger
```

---

## 💾 备份

### 手动备份

```bash
# Docker
cp ./data/ledger.db ./data/ledger-$(date +%Y%m%d).db

# 源码
cp ./ledger.db ./ledger-$(date +%Y%m%d).db
```

### 自动备份（Linux cron）

```bash
# 每天凌晨 3 点备份，保留 30 天
crontab -e
# 加一行：
0 3 * * * cp /path/to/ledger.db /path/to/backups/ledger-$(date +\%Y\%m\%d).db && find /path/to/backups -name "ledger-*.db" -mtime +30 -delete
```

### 自动备份（NAS 推荐）

直接用 NAS 自带的**快照 / 同步 / 备份任务**，把 `data/` 目录定时备份到云盘 / 外接硬盘。**这是最省事的方式**。

---

## 🚚 迁移（换电脑 / 换 NAS / 跨平台）

**整个 Ledger = 一个 `.db` 文件 + 一个镜像/代码**，迁移只需 3 步：

### 场景 A：换 NAS（保持 Docker）

```bash
# 在旧 NAS 上
docker stop ledger
# 复制 ./data/ledger.db 到新 NAS（用 scp / rsync / 共享文件夹）

# 在新 NAS 上
mkdir -p /volume1/docker/ledger/data
# 把 ledger.db 放进去
cd /volume1/docker/ledger
# 准备 docker-compose.yml（同上手册）
docker compose up -d
```

### 场景 B：从 Docker 迁到源码运行

```bash
# 1. 从容器复制数据库出来
docker cp ledger:/data/ledger.db ./

# 2. 在新机器装好源码（git clone + pip install）
# 3. 把 ledger.db 放到项目根目录
# 4. python web/run.py
```

### 场景 C：从源码迁到 Docker

```bash
# 1. 备份当前数据库
cp ./ledger.db ./ledger.db.bak

# 2. 启动容器，挂载包含数据库的目录
docker run -d --name ledger -p 5800:5800 \
  -v $(pwd)/data:/data --restart unless-stopped \
  zouzhenglu/ledger:latest

# 3. 恢复数据
cp ./ledger.db.bak ./data/ledger.db
docker restart ledger
```

### 场景 D：跨 Docker / 跨平台（Windows WSL → Linux NAS）

完全没问题，SQLite 文件**跨平台兼容**。直接复制文件就行。

---

## 🔄 升级会不会丢数据？

**不会。**

升级路径：

| 方式 | 命令 |
|------|------|
| Docker（推荐） | `docker compose pull && docker compose up -d` |
| Docker run | `docker pull ...` 然后重新跑容器（数据卷不变） |
| 源码 | `git pull && pip install -e .` 然后重启服务 |

数据库 schema 由代码自动迁移（`init_db()` 检测版本号），不会丢数据。

如果升级后出问题（极少见）：

```bash
# 回退到上一个版本（Docker）
docker pull zouzhenglu/ledger:0.1.0   # 旧版本号
docker compose down
docker compose up -d
# 数据还在 ./data 里，不会受影响
```

---

## 🔧 数据修复

### 数据库文件损坏（极少发生）

```bash
# 1. 停服务
docker stop ledger

# 2. 备份当前文件（哪怕损坏了也先留着）
cp ./data/ledger.db ./data/ledger.db.broken

# 3. 用 sqlite3 修复
sqlite3 ./data/ledger.db ".recover" | sqlite3 ./data/ledger-recovered.db

# 4. 用 recovered 文件替换
mv ./data/ledger-recovered.db ./data/ledger.db

# 5. 启动
docker start ledger
```

### 想完全清空重新开始

```bash
docker stop ledger
rm ./data/ledger.db
docker start ledger
# 容器会自动创建一个空的数据库
```

---

## 📤 数据导出（交给别人 / 长期归档）

```bash
# 导出全部交易为 JSON
docker exec ledger python scripts/cli.py export --output /data/export.json --format json

# 或者在 Web 界面：交易页 → 导出 → CSV / JSON
```

---

## 🛡 安全建议

| 风险 | 建议 |
|------|------|
| 误删数据库 | 至少保留 3 份异地备份（本地 + 云盘 + 外接硬盘） |
| 数据库文件损坏 | 定期用 `sqlite3 ledger.db "PRAGMA integrity_check;"` 自检 |
| 想加密 | 可以用 [sqlcipher](https://github.com/sqlcipher/sqlcipher)，但需自行编译 |
| 多副本同步冲突 | **不要同时在两台机器上跑同一个 ledger.db**，SQLite 不是分布式数据库 |

---

## ❓ 更多问题

- 容器启动失败 / 端口冲突 → [故障排除](./troubleshooting.md)
- 升级出问题 → [故障排除 → 升级](./troubleshooting.md#升级问题)
- 数据看不见 / 仪表盘空白 → [故障排除 → 数据显示](./troubleshooting.md#数据相关)