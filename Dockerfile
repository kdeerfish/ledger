# ============================================================
# Ledger Dockerfile
# 目标：镜像小、安全、开箱即用
# ============================================================

FROM python:3.11-slim

# ── 元信息 ──
LABEL org.opencontainers.image.title="Ledger"
LABEL org.opencontainers.image.description="个人记账系统 - 收支管理、预算规划、多维度统计"
LABEL org.opencontainers.image.version="1.4.0"
LABEL org.opencontainers.image.source="https://github.com/zouzhenglu/ledger"

# ── 安装依赖 ──
WORKDIR /build
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /build

# ── 创建非 root 用户 ──
RUN groupadd -r ledger && useradd -r -g ledger -d /app -s /sbin/nologin ledger

# ── 复制应用代码 ──
WORKDIR /app
COPY pyproject.toml README.md ./
COPY ledger_modules/ ./ledger_modules/
COPY scripts/ ./scripts/
COPY web/ ./web/

# ── 数据目录（挂载点） ──
RUN mkdir -p /data && chown ledger:ledger /data /app

# ── 切到非 root 用户 ──
USER ledger

VOLUME ["/data"]
EXPOSE 5000

# ── 健康检查 ──
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/health')" || exit 1

# ── 环境变量（可通过 -e 覆盖） ──
ENV WEB_HOST=0.0.0.0
ENV WEB_PORT=5000
ENV WEB_DEBUG=false
ENV LEDGER_DB_PATH=/data/ledger.db

# ── 启动 ──
CMD ["python", "web/run.py"]
