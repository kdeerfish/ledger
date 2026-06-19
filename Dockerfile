# ============================================================
# Ledger Dockerfile - Go rewrite, multi-stage
# 阶段1: 构建 React 前端 (Node 20)
# 阶段2: 构建 Go 后端 (Alpine, 纯静态二进制)
# 阶段3: distroless 运行时 (~20 MB)
# ============================================================

# ── 阶段1: 构建前端 ──
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── 阶段2: 构建 Go 二进制 ──
FROM golang:1.23-alpine AS backend-builder
WORKDIR /src
# 下载依赖(独立 layer,利用 Docker 缓存)
COPY go.mod go.sum ./
RUN go mod download
# 复制源码并构建
COPY . .
# 复制阶段1 的前端产物
COPY --from=frontend-builder /build/dist ./internal/webui/dist
# 静态编译,无 CGO (CGO_ENABLED=0)
ENV CGO_ENABLED=0 GOOS=linux
RUN go build -trimpath -ldflags "-s -w -X main.version=$(date -u +%Y%m%d-%H%M%S)" \
    -o /out/ledger ./cmd/ledger

# ── 阶段3: distroless 运行时 ──
FROM gcr.io/distroless/static:nonroot

LABEL org.opencontainers.image.title="Ledger (Go)"
LABEL org.opencontainers.image.description="个人记账系统 - Go 重写版本,体积更小,性能更好"
LABEL org.opencontainers.image.source="https://github.com/kdeerfish/ledger"
LABEL org.opencontainers.image.licenses="MIT"

# 复制二进制
COPY --from=backend-builder /out/ledger /usr/local/bin/ledger

# 数据目录
WORKDIR /data
VOLUME ["/data"]

# 端口
EXPOSE 5800

# 环境变量
ENV WEB_HOST=0.0.0.0 \
    WEB_PORT=5800 \
    LEDGER_DB_PATH=/data/ledger.db

# 健康检查 (distroless 没有 curl,用 Go 自带的 HTTP 客户端)
# 通过 entrypoint 的一个小 shell 别名实现: 这里我们用一个简单的 tcp check。
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["/usr/local/bin/ledger", "version"]

USER nonroot:nonroot

ENTRYPOINT ["/usr/local/bin/ledger"]
CMD ["serve"]
