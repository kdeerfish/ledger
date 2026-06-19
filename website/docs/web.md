---
sidebar_position: 13
---

# 🌐 Web 管理界面 (Go 版)

Ledger Go 版内置 React 19 + Vite 8 + Bootstrap 5 + Chart.js,**单二进制部署**(前端通过 `embed.FS` 嵌入 Go 二进制),响应式设计,手机 / 平板 / 电脑均可用。

## 启动

```bash
# Docker
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data zouzhenglu/ledger-go

# 二进制
./bin/ledger serve --port 5800
```

浏览器访问 `http://localhost:5800`。

## 页面

| 页面 | 路径 | 功能 |
|------|------|------|
| **概览** | `/` | 收支卡片 + 月度柱状图 + 累计折线图 + 类别环形图(可点击筛选) |
| **交易** | `/transactions` | 多维筛选表格 + 分页 + 编辑 / 软删 / 恢复 / 永久删 |
| **记一笔** | `/add` | 模板选择 + 字段自动建议 + 子类别 + 标签选择器 |
| **预算** | `/budgets` | 总览卡片 + 类别进度条 + 执行明细表 |
| **类别+标签** | `/categories` | 类别层级统计 + 标签创建 / 颜色管理 |
| **统计** | `/stats` | 9 种分组 × 3 种图表,点击跳转交易筛选 |

## 静态资源服务

Go 版把 `frontend/dist` 用 `//go:embed` 嵌进二进制,服务时:

```go
// internal/httpapi/server.go
httpapi.SetFS(webui.FS())  // 启动时注入

// 任何 /api/* 走 JSON API
// 其他路径走 SPA fallback (返回 index.html)
```

**优势**:
- 单文件部署,无需挂载前端目录
- 容器镜像 ~20 MB(原 Python 版 ~110 MB)
- 启动 <50 ms

## 前后端分离开发

```bash
# 终端 1:Go 后端
./bin/ledger serve --port 5800

# 终端 2:Vite dev server (HMR 热更新)
cd frontend && npm run dev
# → http://localhost:5173 (自动代理 /api → :5800)
```

改 React 代码浏览器立即生效,改 Go 代码重启 `bin/ledger` 即可。

## 构建前端

如果改了 React 代码,需要重新构建并嵌入 Go 二进制:

```bash
cd frontend
npm run build   # 输出 frontend/dist
cd ..
go build -o bin/ledger ./cmd/ledger  # embed.FS 自动捕获新 dist
```

或者用 `make build` 一步到位。

## 浏览器兼容性

支持现代浏览器(Chrome 90+、Firefox 90+、Safari 14+、Edge 90+)。

## 移动端

完全响应式,触屏友好。所有功能均可在手机浏览器使用。
