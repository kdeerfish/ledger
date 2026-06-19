---
sidebar_position: 2
---

# 🪟 Docker on WSL（Windows 用户）

> 适用于：Windows 10/11，Docker Desktop 已启用 WSL2 后端（或直接装了 WSL 里的 Docker Engine）。

---

## 0. 前置检查

打开 **PowerShell** 或 **CMD**，确认 Docker 在 WSL 里可用：

```powershell
wsl --status
docker --version
```

应该看到 `Docker version 20.x` 或更高。

:::info 还没装 Docker？
去 [Docker Desktop 官网](https://www.docker.com/products/docker-desktop/) 下载，安装时勾选 **"Use WSL 2 instead of Hyper-V"**。
:::

---

## 1. 一行命令启动

在 **WSL 终端**（不是 PowerShell）执行：

```bash
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger:latest
```

| 参数 | 作用 |
|------|------|
| `-d` | 后台运行 |
| `--name ledger` | 容器名字，方便后续管理 |
| `-p 5800:5800` | 把容器的 5800 端口映射到 Windows 的 5800 |
| `-v $(pwd)/data:/data` | 数据库持久化到当前目录的 `data/` 文件夹 |
| `--restart unless-stopped` | 开机/崩溃自动重启 |

:::tip 国内拉镜像慢？
把镜像换成阿里云：
```bash
docker pull crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ledger:latest
# 然后把上面 docker run 命令里的镜像名换成这个
```
:::

---

## 2. 打开网页

启动成功后（约 3 秒）：

- 浏览器打开：**http://localhost:5800** （Windows 上直接访问，WSL 自动转发）
- 或者在 WSL 里跑 `curl http://localhost:5800/api/health` 验证

看到 React 仪表盘 = 安装成功 🎉

---

## 3. 数据存在哪里？

| 位置 | 路径 |
|------|------|
| WSL 里实际路径 | `~/data/ledger.db`（你执行命令时所在的目录下的 `data/`） |
| Windows 里访问 | `\\wsl$\<发行版名字>\home\<用户名>\data\ledger.db` |

> 例：在 PowerShell 里访问就是 `\\wsl$\Ubuntu\home\你的用户名\data\ledger.db`

### 备份

直接在 Windows 文件管理器复制 `data` 文件夹即可，或者：

```bash
cp -r ~/data ~/data-backup-$(date +%Y%m%d)
```

---

## 4. 用 docker-compose（推荐）

在 WSL 里创建一个项目目录：

```bash
mkdir -p ~/ledger && cd ~/ledger
```

把下面内容保存为 `docker-compose.yml`：

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

启动：

```bash
docker compose up -d
docker compose logs -f
```

以后管理都用 `docker compose` 命令，更简单：

| 命令 | 作用 |
|------|------|
| `docker compose up -d` | 启动 |
| `docker compose down` | 停止 |
| `docker compose restart` | 重启 |
| `docker compose logs -f` | 实时看日志 |
| `docker compose pull && docker compose up -d` | 升级到最新版 |

---

## 5. 升级到新版本

```bash
# docker run 方式
docker pull zouzhenglu/ledger:latest
docker stop ledger && docker rm ledger
# 然后重新跑第 1 步那条 docker run 命令

# docker compose 方式（推荐）
cd ~/ledger
docker compose pull
docker compose up -d
```

数据在 `./data`，**升级不会丢数据**。

---

## 6. 常见问题

### WSL 里访问不到 5800？

WSL2 的 Docker 默认会自动把端口转发到 Windows。如果遇到：

1. 确认 PowerShell 用的不是 Windows 自己的 Docker（要和 WSL 里同一个）
2. 试试用 `http://127.0.0.1:5800`
3. 在 WSL 里跑 `curl http://localhost:5800/api/health` 应该返回 `{"success":true,...}`，能通就说明服务没问题
4. 重启 WSL：`wsl --shutdown` 然后重新打开终端

### 数据想放 Windows 磁盘而不是 WSL？

WSL 访问 Windows 磁盘在 `/mnt/c/` `/mnt/d/` 等。改挂载路径即可：

```bash
docker run -d \
  --name ledger \
  -p 5800:5800 \
  -v /mnt/d/ledger-data:/data \
  --restart unless-stopped \
  zouzhenglu/ledger:latest
```

> ⚠️ 注意：跨系统挂载性能略差，IO 频繁时会比 WSL 内部慢一点，但存数据完全够用。

### 重启电脑后容器没自动起？

检查 Docker Desktop 的设置：**Settings → General → "Start Docker Desktop when you sign in"** 勾选。

---

更多问题见 [FAQ · 故障排除](../faq/troubleshooting.md)。