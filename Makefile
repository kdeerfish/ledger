# ─────────────────────────────────────────────────────────
#  Windows PowerShell 调用兼容层
# ─────────────────────────────────────────────────────────
# GNU Make 4.x 在 Windows 上设置 SHELL = powershell.exe 是不稳定的,
# 会产生 process_begin: CreateProcess(NULL, ...) failed.
# 解决方案:
#   1. SHELL 留作 cmd.exe (Make 的 Windows 默认, 调用稳定)
#   2. .ONESHELL: 整段 recipe 作为一行交给 cmd.exe
#   3. 整段 recipe 只发一条 powershell -NoProfile -Command "<脚本>" 调用
#      脚本内部用 ; 分隔各 PowerShell 语句, 用 ' 包裹路径避免 cmd 转义问题.
# ─────────────────────────────────────────────────────────
.ONESHELL:
.SILENT:

PYTHON := .venv\Scripts\python.exe

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
	powershell -NoProfile -Command "$$p = Resolve-Path 'htmlcov/index.html'; Write-Host ('Coverage report: file:///' + $$p.Path) -ForegroundColor Cyan"

.PHONY: coverage-view
coverage-view:
	powershell -NoProfile -Command "Start-Process (Resolve-Path 'htmlcov/index.html').Path"

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
	powershell -NoProfile -Command "Remove-Item -Recurse -Force '__pycache__','.pytest_cache','htmlcov','.coverage','.coverage.*','build','dist' -ErrorAction SilentlyContinue; Get-ChildItem -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force; Get-ChildItem -Recurse -Filter '*.pyc' -ErrorAction SilentlyContinue | Remove-Item -Force; Write-Host '[clean] all build/cache removed (build/ dist/)'"

.PHONY: clean-db
clean-db:
	powershell -NoProfile -Command "Remove-Item -Force 'ledger.db' -ErrorAction SilentlyContinue; Write-Host '[clean-db] ledger.db removed (tests will recreate)'"

.PHONY: clean-deploy
clean-deploy:
	powershell -NoProfile -Command "Remove-Item -Recurse -Force 'deploy' -ErrorAction SilentlyContinue; Remove-Item -Recurse -Force 'dist' -ErrorAction SilentlyContinue; Remove-Item -Recurse -Force 'build' -ErrorAction SilentlyContinue; Write-Host '[clean-deploy] deploy/dist/build removed'"

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

# ══════════════════════════════════════════════════════════
#  构建 — 统一输出到 deploy/
# ══════════════════════════════════════════════════════════

# ─── 前端构建（公共步骤）─────────────────────────────────
.PHONY: _frontend
_frontend:
	powershell -NoProfile -Command "Write-Host '=== Build frontend ===' -ForegroundColor Cyan"
	cd frontend && cmd /c npm.cmd run build

# ─── Windows 桌面端 ─────────────────────────────────────
.PHONY: build-windows
build-windows: _frontend
	powershell -NoProfile -Command "Write-Host '=== Clean old build ===' -ForegroundColor DarkYellow; Remove-Item -Recurse -Force 'build','dist' -ErrorAction SilentlyContinue"
	powershell -NoProfile -Command "Write-Host '=== PyInstaller packaging ===' -ForegroundColor Cyan"
	$(PYTHON) -m PyInstaller --noconfirm --clean ledger.spec
	powershell -NoProfile -Command "Write-Host '=== Output to deploy/windows/ ===' -ForegroundColor Cyan; Remove-Item -Recurse -Force 'deploy/windows' -ErrorAction SilentlyContinue; New-Item -ItemType Directory -Path 'deploy/windows' -Force | Out-Null; Copy-Item -Recurse 'dist/ledger/*' 'deploy/windows/'"
	powershell -NoProfile -Command "Write-Host '=== Create Ledger.zip ===' -ForegroundColor Cyan; Compress-Archive -Path 'deploy/windows/*' -DestinationPath 'deploy/Ledger.zip' -Force"
	powershell -NoProfile -Command "Write-Host ''; Write-Host '  OK deploy/windows/    (EXE dir)' -ForegroundColor Green; Write-Host '  OK deploy/Ledger.zip  (installer)' -ForegroundColor Green"

# ─── Docker 服务端 ──────────────────────────────────────
.PHONY: build-docker
build-docker: _frontend
	powershell -NoProfile -Command "Write-Host '=== Prepare Docker build context ===' -ForegroundColor Cyan; Remove-Item -Recurse -Force 'deploy/docker' -ErrorAction SilentlyContinue; New-Item -ItemType Directory -Path 'deploy/docker' -Force | Out-Null; Copy-Item -Recurse 'ledger_modules' 'deploy/docker/ledger_modules' -Exclude '__pycache__'; Copy-Item -Recurse 'web' 'deploy/docker/web' -Exclude '__pycache__'; Copy-Item -Recurse 'scripts' 'deploy/docker/scripts' -Exclude '__pycache__'; New-Item -ItemType Directory -Path 'deploy/docker/frontend/dist' -Force | Out-Null; Copy-Item -Recurse 'frontend/dist/*' 'deploy/docker/frontend/dist/'; Copy-Item 'requirements.txt' 'deploy/docker/'; Copy-Item 'pyproject.toml' 'deploy/docker/'; Copy-Item 'Dockerfile' 'deploy/docker/'; Copy-Item 'docker-compose.yml' 'deploy/docker/'; Copy-Item '.env.example' 'deploy/docker/' -ErrorAction SilentlyContinue"
	powershell -NoProfile -Command "Write-Host '=== Create ledger-service.zip ===' -ForegroundColor Cyan; Compress-Archive -Path 'deploy/docker/*' -DestinationPath 'deploy/ledger-service.zip' -Force"
	powershell -NoProfile -Command "Write-Host ''; Write-Host '  OK deploy/docker/              (Docker context)' -ForegroundColor Green; Write-Host '  OK deploy/ledger-service.zip   (service pack)' -ForegroundColor Green"

# ─── AI 技能包 ──────────────────────────────────────────
.PHONY: build-skills
build-skills:
	powershell -NoProfile -Command "Write-Host '=== Package AI skills ===' -ForegroundColor Cyan; Remove-Item -Recurse -Force 'deploy/ledger-skills' -ErrorAction SilentlyContinue; New-Item -ItemType Directory -Path 'deploy/ledger-skills' -Force | Out-Null; Copy-Item -Recurse 'skills/ledger/scripts' 'deploy/ledger-skills/scripts' -Exclude '__pycache__'; Copy-Item 'skills/ledger/SKILL.md' 'deploy/ledger-skills/'; Copy-Item 'skills/ledger/.env.example' 'deploy/ledger-skills/' -ErrorAction SilentlyContinue; if (Test-Path 'skills/ledger/references') { Copy-Item -Recurse 'skills/ledger/references' 'deploy/ledger-skills/references' }; if (Test-Path 'skills/ledger/examples') { Copy-Item -Recurse 'skills/ledger/examples' 'deploy/ledger-skills/examples' }; Compress-Archive -Path 'deploy/ledger-skills/*' -DestinationPath 'deploy/ledger-skills.zip' -Force"
	powershell -NoProfile -Command "Write-Host ''; Write-Host '  OK deploy/ledger-skills/       (skill dir)' -ForegroundColor Green; Write-Host '  OK deploy/ledger-skills.zip    (skill pack)' -ForegroundColor Green"

# ─── 全部构建 ──────────────────────────────────────────
.PHONY: build
build: build-windows build-docker build-skills
	powershell -NoProfile -Command "Copy-Item 'DEPLOY.md' 'deploy/' -ErrorAction SilentlyContinue; Write-Host ''; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '  All builds complete! Output: deploy/' -ForegroundColor Green; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; Get-ChildItem 'deploy' | Format-Table Name, @{L='Size';E={if($$_.PSIsContainer){'<DIR>'}else{'{0:N0} KB' -f ($$_.Length/1KB)}}} -AutoSize"

# ─── 部署（兼容旧命令）─────────────────────────────────
.PHONY: deploy
deploy: build

# ─── 发版 ──────────────────────────────────────────────
.PHONY: release
release:
	$(PYTHON) scripts/release.py $(filter-out $@,$(MAKECMDGOALS))

.PHONY: release-dry
release-dry:
	$(PYTHON) scripts/release.py --dry-run $(filter-out $@,$(MAKECMDGOALS))

# ─── Windows 服务管理 ──────────────────────────────────
.PHONY: service-install
service-install:
	powershell -ExecutionPolicy Bypass -File scripts\win_service.ps1 -Action install

.PHONY: service-uninstall
service-uninstall:
	powershell -ExecutionPolicy Bypass -File scripts\win_service.ps1 -Action uninstall

.PHONY: service-start
service-start:
	powershell -ExecutionPolicy Bypass -File scripts\win_service.ps1 -Action start

.PHONY: service-stop
service-stop:
	powershell -ExecutionPolicy Bypass -File scripts\win_service.ps1 -Action stop

.PHONY: service-status
service-status:
	powershell -ExecutionPolicy Bypass -File scripts\win_service.ps1 -Action status

# ─── Help ───────────────────────────────────────────────
.PHONY: help
help:
	powershell -NoProfile -Command "Write-Host ''; Write-Host 'Ledger project commands' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; Write-Host '  Testing:'; Write-Host '    make test            Run all tests'; Write-Host '    make test-quick      Quick tests (short output)'; Write-Host '    make coverage        Tests + coverage report'; Write-Host '    make lint            Lint code'; Write-Host '    make format          Format code'; Write-Host ''; Write-Host '  Build (output to deploy/):' -ForegroundColor Cyan; Write-Host '    make build           All builds (Windows + Docker + Skills)'; Write-Host '    make build-windows   Windows desktop only (EXE + ZIP)'; Write-Host '    make build-docker    Docker server only (context + ZIP)'; Write-Host '    make build-skills    AI skill pack'; Write-Host '    make clean-deploy    Clean build artifacts'; Write-Host ''; Write-Host '  Release:' -ForegroundColor Cyan; Write-Host '    make release         Package + git tag + Gitea Release'; Write-Host '    make release-dry     Package only, no release'; Write-Host ''; Write-Host '  Windows service:' -ForegroundColor Cyan; Write-Host '    make service-install   Register as Windows service'; Write-Host '    make service-uninstall Uninstall service'; Write-Host '    make service-start     Start service'; Write-Host '    make service-stop      Stop service'; Write-Host '    make service-status    Show service status'; Write-Host ''; Write-Host '  Tools:' -ForegroundColor Cyan; Write-Host '    make cli             CLI entry: make cli list'; Write-Host '    make import          Import CSV: make import data.csv'; Write-Host '    make install         Install dev deps'; Write-Host '    make clean           Clean cache files'; Write-Host '========================================' -ForegroundColor Cyan"
