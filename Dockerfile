# ============================================================
# Ledger Dockerfile - 多阶段构建
# 阶段1: 构建 React 前端
# 阶段2: Python 运行环境
# ============================================================

# ── 阶段1: 构建前端 ──
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# 先安装依赖（利用 Docker 缓存）
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# 复制并构建
COPY frontend/ ./
RUN npm run build

# ── 阶段2: Python 运行环境 ──
FROM python:3.11-alpine

# ── 元信息 ──
LABEL org.opencontainers.image.title="Ledger"
LABEL org.opencontainers.image.description="个人记账系统 - 收支管理、预算规划、多维度统计"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/kdeerfish/ledger"

# ── 安装 Python 依赖 ──
WORKDIR /build
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /build

# ── 创建非 root 用户（UID=1000 兼容飞牛OS/Synology 等 NAS 环境） ──
RUN addgroup -g 1000 ledger && adduser -u 1000 -G ledger -h /app -s /sbin/nologin -D ledger

# ── 复制应用代码 ──
WORKDIR /app
COPY pyproject.toml README.md ./
COPY ledger_modules/ ./ledger_modules/
COPY scripts/ ./scripts/
COPY web/ ./web/

# ── 复制构建好的前端 ──
COPY --from=frontend-builder /build/dist ./frontend/dist/

# ── 数据目录（挂载点） ──
RUN mkdir -p /data && chown ledger:ledger /data /app

# ── 切到非 root 用户 ──
USER ledger

VOLUME ["/data"]
EXPOSE 5800

# ── 健康检查 ──
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5800/api/health')" || exit 1

# ── 环境变量 ──
ENV WEB_HOST=0.0.0.0
ENV WEB_PORT=5800
ENV WEB_DEBUG=false
ENV LEDGER_DB_PATH=/data/ledger.db

# ── 启动（生产模式，直接服务构建好的前端） ──
CMD ["python", "web/run.py"]
