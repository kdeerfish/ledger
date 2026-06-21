---
sidebar_position: 4
---

# 🔗 Docker 容器间网络互通

> 适用场景：Agent（如 picoclaw）和 Ledger 记账服务**都运行在 Docker 容器中**，需要让 Agent 能访问 Ledger 的 API（默认端口 5800）。

---

## 先搞清楚问题

Docker 容器有自己独立的网络，默认情况下：

- **容器内** `localhost` 只指向容器自己，不是宿主机
- 所以 Agent 容器里写 `http://localhost:5800` **访问不到** Ledger 容器

下面按部署方式从简到繁，选适合你的方案。

---

## 方案一览

| 方案 | 适用场景 | 改动量 | 稳定性 |
|------|----------|--------|--------|
| **A. 同一 docker-compose** | 新部署，或能接受合并编排 | ⭐ 一行配置 | ⭐⭐⭐⭐⭐ |
| **B. 共享 Docker 网络** | 已有独立容器，不想重建 | ⭐⭐ 两条命令 | ⭐⭐⭐⭐⭐ |
| **C. LAN IP + 端口映射** | 跨宿主机 / 不便操作网络 | ⭐ 一行配置 | ⭐⭐⭐ |
| **D. Docker 网桥网关** | 不想改容器配置 | ⭐⭐ 需确认网关 IP | ⭐⭐ |

---

## 方案 A：同一 docker-compose 部署（推荐新用户）

最省心的做法。把两个服务写进同一个 `docker-compose.yml`，Docker Compose 会自动创建共享网络，**服务名即主机名**。

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

  agent:
    image: 你的agent镜像
    container_name: agent
    restart: unless-stopped
    environment:
      - LEDGER_API_URL=http://ledger:5800   # 👈 用服务名访问
```

启动后，Agent 容器里直接用 `http://ledger:5800` 就能访问 Ledger。

```bash
docker compose up -d
# 验证
docker exec agent curl http://ledger:5800/api/health
```

:::tip 为什么能通？
同一个 `docker-compose.yml` 里的服务自动共享一个网络，Docker 内置 DNS 会把 `ledger` 解析为 Ledger 容器的内部 IP。
:::

---

## 方案 B：共享 Docker 网络（已有独立容器）

两个容器已经分别跑着，不想重建？事后也能连到一起。

### 步骤

```bash
# 1. 创建共享网络
docker network create ledger-net

# 2. 把两个容器都连进去
docker network connect ledger-net ledger
docker network connect ledger-net agent
```

然后设置 Agent 的环境变量：

```bash
LEDGER_API_URL=http://ledger:5800
```

### 验证

```bash
docker exec agent curl http://ledger:5800/api/health
```

:::note 重启后会丢失吗？
`docker network connect` 是运行时操作，容器重启后会自动重新连上。但**宿主机重启后**需要确保网络存在——用 `docker-compose` 或写成启动脚本更稳。
:::

---

## 方案 C：LAN IP + 端口映射（跨宿主机）

两个容器在**不同的机器**上，或者你不想动 Docker 网络配置。

### 原理

Ledger 启动时已经通过 `-p 5800:5800` 把端口映射到了宿主机。任何能访问宿主机的设备（包括同一局域网里的其他容器）都能通过宿主机 IP 访问。

### 配置

```bash
# 假设 Ledger 所在宿主机的局域网 IP 是 192.168.x.x
LEDGER_API_URL=http://192.168.x.x:5800
```

在 Agent 容器启动时传入：

```bash
docker run -d \
  --name agent \
  -e LEDGER_API_URL=http://192.168.x.x:5800 \
  你的agent镜像
```

或者在 `docker-compose.yml` 里：

```yaml
agent:
  environment:
    - LEDGER_API_URL=http://192.168.x.x:5800
```

### 如何让 IP 永不变？

在路由器管理页面找到 **DHCP 静态绑定**（也叫"IP 与 MAC 绑定"、"静态地址分配"），给 NAS 的 MAC 地址绑一个固定 IP。各品牌路由器路径：

| 路由器 | 路径 |
|--------|------|
| 小米 | 路由设置 → DHCP → IP 与 MAC 绑定 |
| TP-Link | 路由设置 → DHCP 设置 → 静态地址分配 |
| 华硕 | LAN → DHCP → 手动指定 IP |
| OpenWrt | 网络 → DHCP → 静态租约 |

:::warning 注意
如果 NAS 换了网口或连了不同的路由器，MAC 地址会变，需要重新绑定。
:::

---

## 方案 D：Docker 网桥网关（不改容器网络）

Docker 默认网桥的网关 IP（通常是 `172.17.0.1`）就是宿主机在容器网络里的地址，容器可以通过它访问宿主机上映射的端口。

### 查看你的网关 IP

```bash
# 在宿主机上查看 docker0 网桥的 IP
ip addr show docker0 | grep "inet "
# 输出类似：inet 172.17.0.1/16

# 或者在容器内查看默认网关
docker exec agent ip route | grep default
# 输出类似：default via 172.17.0.1 dev eth0
```

### 配置

```bash
# 用查到的网关 IP
LEDGER_API_URL=http://172.17.0.1:5800
```

### ⚠️ 这个 IP 可能会变

以下情况网关 IP 可能改变：

- Docker 服务重启，且 `172.17.0.0/16` 网段被占用
- 不同 NAS 系统的默认网桥网段不同（群晖、威联通可能不是 `172.17.0.0`）
- 重建了 Docker 网络

### 固定网桥网关（可选）

在宿主机上编辑 `/etc/docker/daemon.json`：

```json
{
  "bip": "172.17.0.1/16"
}
```

重启 Docker：

```bash
sudo systemctl restart docker
```

:::caution 重启 Docker 会中断所有运行中的容器
操作前确认没有重要服务在跑，或者有自动重启策略（`restart: unless-stopped`）。
:::

---

## 四种方案对比总结

```
                  ┌─────────────────────────────┐
                  │  两个容器在同一台宿主机？     │
                  └──────────────┬──────────────┘
                          ┌─── Yes ───┐
                          │           │
                          ▼           ▼
                   能合并成一个       已经是独立容器
                   docker-compose？   不想重建
                          │           │
                     ┌─ Yes ┘         └─ No ─┐
                     ▼                       ▼
               方案 A（最简单）          方案 B（共享网络）
                                               
          ┌──── 不同宿主机 / 不想动网络 ────┐
          ▼                                ▼
    知道 LAN IP 且稳定？             不确定 IP 会变？
          │                                │
     ┌─ Yes ┘                           ┌─ No ┘
     ▼                                  ▼
  方案 C（LAN IP）                方案 D（网桥网关）
  + 路由器绑 IP                   + daemon.json 固定
```

---

## 常见问题

### Agent 里报 `Connection refused`？

```bash
# 1. 确认 Ledger 容器在跑
docker ps | grep ledger

# 2. 从宿主机测试
curl http://localhost:5800/api/health

# 3. 从 Agent 容器内部测试（替换为你的实际地址）
docker exec agent curl http://ledger:5800/api/health   # 方案 A/B
docker exec agent curl http://192.168.x.x:5800/api/health  # 方案 C
```

### DNS 解析失败（`Could not resolve host`）？

说明两个容器不在同一个 Docker 网络里。用方案 B 把它们连到同一个网络。

### 用容器名访问不到？

- 确认两个容器在**同一个 Docker 网络**里（方案 A 自动满足，方案 B 需要手动连）
- 容器名必须和 `container_name` 或服务名一致
- 用 `docker network inspect ledger-net` 查看网络里的容器列表

---

更多问题见 [FAQ · 故障排除](../faq/troubleshooting.md)。
