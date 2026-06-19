---
sidebar_position: 3
---

# 💾 Docker on NAS（飞牛OS / 群晖 / unRAID）

> 适用于：飞牛OS (FnOS)、群晖 DSM、威联通、unRAID、或者任何装了 Container Station / Docker 的 Linux NAS。

NAS 部署的好处：**7×24 小时在线**，家里所有设备（手机/电脑）都能访问同一个数据。

---

## 0. 前置检查

SSH 登录到你的 NAS（飞牛OS 默认账号 `admin`）：

```bash
ssh admin@你的NAS_IP
docker --version
```

能输出版本号就行。

---

## 1. 创建数据目录

```bash
# 飞牛OS 推荐路径
mkdir -p /volume1/docker/ledger/data
cd /volume1/docker/ledger
```

> 群晖路径通常是 `/volume1/docker/...`，威联通 `/share/Container/...`，按你的实际存储池改。

---

## 2. 准备 docker-compose.yml

在该目录下新建 `docker-compose.yml`：

```yaml
services:
  ledger:
    image: zouzhenglu/ledger:latest
    container_name: ledger
    restart: unless-stopped
    ports:
      - "5800:5800"
    volumes:
      - ./data:/data
    environment:
      - WEB_HOST=0.0.0.0
      - WEB_PORT=5800
      - TZ=Asia/Shanghai
```

可选：新建 `.env` 自定义配置（一般不用）：

```bash
# Web 端口改成别的（避免和 NAS 其他服务冲突）
# WEB_PORT=5800

# 数据库路径（一般不用改）
# LEDGER_DB_PATH=/data/ledger.db
```

---

## 3. 启动

```bash
cd /volume1/docker/ledger
docker compose up -d
docker compose logs -f
```

看到 `Running on http://0.0.0.0:5800` 就是启动成功，按 `Ctrl+C` 退出日志（容器继续跑）。

---

## 4. 打开网页

在 **同一局域网** 的电脑/手机浏览器：

```
http://你的NAS_IP:5800
```

例如：`http://192.168.1.100:5800`

:::tip 不知道 NAS IP？
在 NAS 控制台的网络设置看，或者 SSH 里跑 `ip addr | grep "inet "`。
:::

---

## 5. 数据在哪？怎么备份？

| 项目 | 路径 |
|------|------|
| 数据库 | `/volume1/docker/ledger/data/ledger.db` |
| 整个数据目录 | `/volume1/docker/ledger/data/` |

### 备份（推荐用 NAS 自带的快照/同步任务）

手动备份：

```bash
cp /volume1/docker/ledger/data/ledger.db \
   /volume1/backup/ledger-$(date +%Y%m%d).db
```

或者直接同步 `data/` 文件夹到云盘。

---

## 6. 飞牛OS 图形化部署（不用命令行）

飞牛OS 有图形化的 Docker 管理面板，更适合不熟命令行的用户：

1. 打开 **飞牛OS → Docker → 项目 → 新建**
2. 项目名：`ledger`
3. 路径：选你创建的 `/docker/ledger` 目录
4. 来源：**创建 docker-compose.yml**，粘贴上面第 2 步的内容
5. 点 **部署**
6. 等 30 秒，浏览器打开 `http://NAS_IP:5800`

---

## 7. 群晖 DSM 部署

1. 打开 **Container Manager**（以前叫 Docker）
2. **项目 → 新增**
3. 路径选你建好的文件夹，docker-compose.yml 粘贴上面的内容
4. 部署

DSM 的 Container Manager 自动接管 docker compose 命令。

---

## 8. 升级

```bash
cd /volume1/docker/ledger
docker compose pull            # 拉新镜像
docker compose up -d           # 重启容器，自动用新镜像
```

数据卷 `./data` 没动，**绝不丢数据**。

---

## 9. 局域网外访问（可选）

如果想在公司也能访问家里的 NAS，**不推荐直接把 5800 端口暴露到公网**。建议：

| 方案 | 推荐度 | 复杂度 |
|------|--------|--------|
| VPN（WireGuard / Tailscale） | ⭐⭐⭐⭐⭐ | 低 |
| NAS 自带的 DDNS + 反向代理 | ⭐⭐⭐ | 中 |
| Cloudflare Tunnel | ⭐⭐⭐⭐ | 中 |
| 直接端口映射到公网 | ⭐ | — |

---

## 10. 常见问题

### 端口被占用？

报错 `bind: address already in use`，说明 5800 端口被别的服务用了。两种解法：

```bash
# 解法 1：改 ledger 端口（推荐）
# 在 docker-compose.yml 里把 "5800:5800" 改成 "15800:5800"
# 然后浏览器用 NAS_IP:15800 访问

# 解法 2：找占用 5800 的进程
sudo lsof -i :5800
```

### 启动后浏览器访问不了？

```bash
# 1. 看容器是否在跑
docker ps | grep ledger

# 2. 看日志找错误
docker compose logs --tail=50

# 3. 测试端口
curl http://NAS_IP:5800/api/health
```

### 时区不对？

`docker-compose.yml` 里已经设了 `TZ=Asia/Shanghai`，按需改成你所在的时区。

---

更多问题见 [FAQ · 故障排除](../faq/troubleshooting.md)。