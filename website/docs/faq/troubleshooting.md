---
sidebar_position: 9
---

# 🔧 故障排除

按症状查问题，每个问题都给了「诊断 → 解决」两步。

---

## 🚨 启动相关

### 容器启动后立刻退出

```bash
docker compose logs ledger
```

常见原因：

| 报错关键词 | 原因 | 解决 |
|----------|------|------|
| `bind: address already in use` | 端口被占 | 改 `docker-compose.yml` 里端口 |
| `permission denied` on `/data` | 数据目录权限 | `chmod 777 ./data` 或改挂载路径 |
| `database is locked` | 上次没正常退出 | `docker restart ledger` |
| `no space left on device` | 磁盘满了 | 清理 Docker：`docker system prune` |

---

### 端口被占用

```bash
# 找出谁占着
# Linux/macOS
sudo lsof -i :5800
# Windows
netstat -ano | findstr :5800

# 解法：换成别的端口（容器内部 5800 不变）
# docker-compose.yml
ports:
  - "15800:5800"   # 改宿主机端口
```

然后浏览器用 `http://localhost:15800` 访问。

---

## 🌐 访问相关

### 浏览器打不开页面

**诊断步骤**：

```bash
# 1. 容器在跑吗？
docker ps | grep ledger
# 没输出 = 容器没启动，docker compose up -d

# 2. 容器里服务正常吗？
docker exec ledger curl -s http://localhost:5800/api/health
# 期望：{"success":true,"data":{"status":"ok"}}

# 3. 端口转发对吗？
docker port ledger
# 期望：5800/tcp -> 0.0.0.0:5800

# 4. 防火墙？
# Linux: sudo ufw allow 5800/tcp
# 群晖: 控制面板 → 安全性 → 防火墙 → 编辑规则
# Windows: 控制面板 → Windows Defender 防火墙 → 高级设置 → 入站规则
```

---

### WSL 用户访问不到 localhost:5800

WSL2 默认会自动转发端口到 Windows。如果不行：

```powershell
# 1. 更新 WSL
wsl --update

# 2. 重启 Docker Desktop

# 3. 在 WSL 里测一下
wsl
curl http://localhost:5800/api/health
# 能通 = WSL 里没问题，问题在 Windows 端口转发
```

---

### NAS 用户局域网访问不到

```bash
# 在 NAS 上测
curl http://NAS_IP:5800/api/health

# 在你的电脑上测（NAS_IP 换成实际 IP）
ping NAS_IP
curl http://NAS_IP:5800/api/health
```

不通用：

| 场景 | 解决 |
|------|------|
| ping 不同 | 不在同一个局域网 / 子网掩码问题 |
| ping 通但 curl 不通 | NAS 防火墙阻挡 5800 端口 |
| 能 curl 但浏览器不行 | 浏览器代理 / DNS 污染问题，换 `http://` 而非 `https://` |

---

### 局域网外访问（人在公司想看家里的账）

**不要直接把 5800 端口暴露公网**。推荐方案：

1. **Tailscale**（最简单）：NAS 和电脑都装，自动组网，访问 `http://100.x.x.x:5800`
2. **WireGuard VPN**：自己搭，几行配置
3. **Cloudflare Tunnel**：免费，不用开放端口
4. **NAS 自带的 VPN 服务器**：群晖/飞牛OS 都有

---

## 🐢 性能相关

### Web 界面加载慢

```bash
# 1. 看容器资源占用
docker stats ledger

# 2. 数据库太大？
ls -lh ./data/ledger.db
# 几百 MB 以内都正常；几个 G 就考虑归档历史数据

# 3. 网络慢？
# NAS 用户：从局域网访问（不要走外网）
```

---

### 数据多时筛选慢

Ledger 数据库用 SQLite + 索引，几万条数据流畅。**几十万条以上**才可能感觉慢。

优化方法：

```bash
# 1. 用 vacuum 整理
sqlite3 ./data/ledger.db "VACUUM;"

# 2. 归档老数据：导出 → 软删除 → 看汇总用 stats

# 3. 确认索引存在
sqlite3 ./data/ledger.db ".schema transactions"
```

---

## 数据相关

### 看不到刚记的交易

可能原因：

| 现象 | 原因 | 解决 |
|------|------|------|
| 列表空白 | 筛选条件太严 | 清空筛选 |
| 列表空但 API 能查到 | 浏览器缓存 | Ctrl+Shift+R 强制刷新 |
| API 也查不到 | 没真保存 | 重试 + 看容器日志 |

---

### 重复数据

`add` 命令会自动检测重复（同类型/同金额/同日期/同类目）。如果还出现重复：

```bash
# 找出所有重复
sqlite3 ./data/ledger.db "
SELECT type, amount, category, date, COUNT(*) as cnt
FROM transactions
WHERE is_deleted = 0
GROUP BY type, amount, category, date
HAVING cnt > 1;
"

# 手动删（用 CLI 的 hard_delete）
python scripts/cli.py hard_delete --id <ID> --confirm
```

---

### 类别打错了，懒得一条条改

CLI 批量改（开发者用）：

```bash
sqlite3 ./data/ledger.db "
UPDATE transactions
SET category = '餐饮'
WHERE category = '食品酒水';
"
```

⚠️ 操作前先备份数据库。

---

## 升级问题

### 升级后容器起不来

```bash
# 1. 看错误
docker compose logs ledger

# 2. 常见：磁盘满、端口冲突、数据文件被锁
df -h                # 看磁盘
docker ps -a         # 看是不是已有同名容器没删

# 3. 回退版本
# docker-compose.yml
image: zouzhenglu/ledger:0.1.0   # 用上一个版本号
docker compose up -d
```

---

### 升级后数据格式不对（基本不会发生）

Ledger 用 `init_db()` 自动迁移。如果万一出问题：

```bash
# 1. 停服务
docker stop ledger

# 2. 备份当前数据库
cp ./data/ledger.db ./data/ledger-broken.db

# 3. 找一台没升级的旧版本，启动，把数据导成 JSON
docker run -d --name ledger-old -p 5801:5800 -v ./data-backup:/data zouzhenglu/ledger:0.1.0
curl http://localhost:5801/api/export?format=json -o ledger-export.json

# 4. 停旧版本，用新版本，重新导入（暂时需要手动 SQL）
# 或者回到旧版本
```

---

## 🤖 Agent 相关

### Agent 连不上 Ledger API

```bash
# 1. 确认 Ledger 在跑
curl http://localhost:5800/api/health

# 2. 确认 Agent 配置的 URL 对
cat ~/.picoclaw/skills/ledger/.env
# 应该是 LEDGER_API_URL=http://localhost:5800（本地）
# 或 LEDGER_API_URL=http://NAS_IP:5800（远程）

# 3. 如果 Agent 跑在不同机器，确认端口可达
# 从 Agent 机器：curl http://NAS_IP:5800/api/health
```

---

### Agent 调 add 报错

最常见的错误：`{"success":false,"error":"重复交易"}`

加 `"force": true` 跳过重复检查：

```bash
python3 ledger_cli.py add '{"type":"支出","amount":30,"category":"食品","force":true}'
```

---

## 🛠 调试技巧

### 进容器看内部

```bash
# 进入容器 shell
docker exec -it ledger bash

# 看进程
docker top ledger

# 看资源占用
docker stats ledger

# 看环境变量
docker exec ledger env
```

---

### 看详细日志

```bash
# 实时日志
docker compose logs -f

# 最近 100 行
docker compose logs --tail=100

# 启用 Web 调试模式（开发用，会更详细）
# docker-compose.yml 加环境变量：
# - WEB_DEBUG=true
```

---

### 完全重置（保留数据）

```bash
docker compose down        # 停容器
docker compose up -d       # 重启，数据还在
```

### 完全重置（清空数据）

```bash
docker compose down -v     # 警告：-v 会删挂载卷
docker compose up -d
```

---

## ❓ 还没解决？

- 提交 Issue: [https://github.com/kdeerfish/ledger/issues](https://github.com/kdeerfish/ledger/issues)
- 带上 `docker compose logs` 输出
- 带上你的部署方式（WSL/NAS/源码）和操作系统版本