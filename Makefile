SHELL = powershell.exe
PYTHON = python

# ─── Testing ────────────────────────────────────────────
.PHONY: test
test:
	$(PYTHON) -m pytest tests -v

.PHONY: test-quick
test-quick:
	$(PYTHON) -m pytest tests -v --tb=short -q

.PHONY: test-match
test-match:
	$(PYTHON) -m pytest tests -v -k "$(filter-out $@,$(MAKECMDGOALS))"

# ─── Coverage ────────────────────────────────────────────
.PHONY: coverage
coverage:
	$(PYTHON) -m pytest tests --cov=ledger_modules --cov=scripts --cov-report=term --cov-report=html
	@Write-Host "Coverage report: file:///$(shell Resolve-Path htmlcov/index.html)"

.PHONY: coverage-view
coverage-view:
	Start-Process "$(shell Resolve-Path htmlcov/index.html)"

# ─── Lint ────────────────────────────────────────────────
.PHONY: lint
lint:
	$(PYTHON) -m ruff check ledger_modules scripts tests

.PHONY: lint-fix
lint-fix:
	$(PYTHON) -m ruff check --fix ledger_modules scripts tests

.PHONY: format
format:
	$(PYTHON) -m ruff format ledger_modules scripts tests

# ─── Clean ──────────────────────────────────────────────
.PHONY: clean
clean:
	Remove-Item -Recurse -Force __pycache__, .pytest_cache, htmlcov, .coverage, .coverage.* -ErrorAction SilentlyContinue
	Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
	Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force

.PHONY: clean-db
clean-db:
	Remove-Item -Force ledger.db -ErrorAction SilentlyContinue
	Write-Host "数据库已删除（重新运行测试会自动创建）"

# ─── Run ────────────────────────────────────────────────
.PHONY: cli
cli:
	$(PYTHON) scripts/cli.py $(filter-out $@,$(MAKECMDARGV))

.PHONY: import
import:
	$(PYTHON) scripts/import_ledger.py $(filter-out $@,$(MAKECMDARGV))

# ─── Install ────────────────────────────────────────────
.PHONY: install
install:
	pip install -e ".[dev,lint]"

# ─── Help ───────────────────────────────────────────────
.PHONY: help
help:
	@Write-Host ""
	@Write-Host "Ledger 项目命令"
	@Write-Host "═══════════════════════════════════════"
	@Write-Host "make test         运行所有测试"
	@Write-Host "make test-quick   快速测试（简略输出）"
	@Write-Host "make test-match  模糊匹配测试名: make test-match test_budget"
	@Write-Host "make coverage    运行测试并生成覆盖率报告"
	@Write-Host "make lint        代码检查"
	@Write-Host "make lint-fix    自动修复代码问题"
	@Write-Host "make format      格式化代码"
	@Write-Host "make clean       清理缓存文件"
	@Write-Host "make install     安装开发依赖"
	@Write-Host "make cli         CLI 入口: make cli list"
	@Write-Host "make import      导入CSV: make import data.csv"
	@Write-Host "═══════════════════════════════════════"
