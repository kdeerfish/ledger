<#
.SYNOPSIS
    Ledger 一键打包脚本
.DESCRIPTION
    自动完成：构建前端 → 安装依赖 → PyInstaller 打包 → 输出到 dist/
.EXAMPLE
    .\scripts\build.ps1              # 标准打包
    .\scripts\build.ps1 -Clean       # 清理后重新打包
    .\scripts\build.ps1 -OneFile     # 打包成单个 exe
#>

param(
    [switch]$Clean,
    [switch]$OneFile,
    [switch]$SkipFrontend,
    [switch]$Service,        # 打包后自动注册为服务
    [int]$Port = 5800
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "=" * 55
Write-Host "  Ledger Build Script"
Write-Host "=" * 55
Write-Host ""

# ─── 1. 前置检查 ─────────────────────────────────────

Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Cyan

# 检查 Python
try {
    $pyVer = python --version 2>&1
    Write-Host "  Python: $pyVer" -ForegroundColor Gray
} catch {
    Write-Host "  [ERROR] Python not found!" -ForegroundColor Red
    exit 1
}

# 检查/安装 PyInstaller
$hasPyInstaller = python -c "import PyInstaller" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller --quiet
}

# 检查/安装 pywebview
$hasWebview = python -c "import webview" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing pywebview..." -ForegroundColor Yellow
    pip install pywebview --quiet
}

# ─── 2. 清理旧构建 ──────────────────────────────────

if ($Clean) {
    Write-Host "[2/6] Cleaning old builds..." -ForegroundColor Cyan
    $dirs = @("build", "dist", "__pycache__")
    foreach ($d in $dirs) {
        $path = Join-Path $RootDir $d
        if (Test-Path $path) {
            Remove-Item -Recurse -Force $path
            Write-Host "  Removed: $d" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "[2/6] Skipping clean (use -Clean to force)" -ForegroundColor Gray
}

# ─── 3. 构建前端 ─────────────────────────────────────

Write-Host "[3/6] Building frontend..." -ForegroundColor Cyan

$frontendDir = Join-Path $RootDir "frontend"
if (-not $SkipFrontend -and (Test-Path "$frontendDir\package.json")) {
    Push-Location $frontendDir
    try {
        # 安装依赖
        if (-not (Test-Path "node_modules")) {
            Write-Host "  Installing npm dependencies..." -ForegroundColor Gray
            npm install --silent 2>&1 | Out-Null
        }
        # 构建
        Write-Host "  Running vite build..." -ForegroundColor Gray
        npm run build 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed"
        }
        Write-Host "  Frontend built: frontend/dist/" -ForegroundColor Green
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  Frontend build skipped or not found" -ForegroundColor Gray
}

# ─── 4. 检查前端产物 ─────────────────────────────────

$distDir = Join-Path $RootDir "frontend\dist"
if (-not (Test-Path "$distDir\index.html")) {
    Write-Host "  [WARN] frontend/dist/index.html not found" -ForegroundColor Yellow
    Write-Host "  The exe will use Flask template fallback" -ForegroundColor Yellow
}

# ─── 5. PyInstaller 打包 ─────────────────────────────

Write-Host "[4/6] Running PyInstaller..." -ForegroundColor Cyan

$specFile = Join-Path $RootDir "ledger.spec"
$buildArgs = @(
    "pyinstaller"
    "--noconfirm"            # 覆盖旧产物
    "--clean"                # 清理缓存
)

if ($OneFile) {
    $buildArgs += "--onefile"
    $buildArgs += "--name"
    $buildArgs += "ledger-standalone"
} else {
    # 使用 spec 文件（文件夹模式，启动更快）
    $buildArgs += $specFile
}

Write-Host "  Command: $($buildArgs -join ' ')" -ForegroundColor Gray
& $buildArgs[0] $buildArgs[1..($buildArgs.Length-1)]

if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] PyInstaller failed!" -ForegroundColor Red
    exit 1
}

# ─── 6. 输出结果 ─────────────────────────────────────

Write-Host "[5/6] Build complete!" -ForegroundColor Cyan

if ($OneFile) {
    $outputExe = Join-Path $RootDir "dist\ledger-standalone.exe"
} else {
    $outputExe = Join-Path $RootDir "dist\ledger\ledger.exe"
}

if (Test-Path $outputExe) {
    $size = [math]::Round((Get-Item $outputExe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "  Output: $outputExe" -ForegroundColor Green
    Write-Host "  Size:   ${size} MB" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Output exe not found at expected path" -ForegroundColor Yellow
}

# 复制 .env 到 dist 目录（如果有）
$envSrc = Join-Path $RootDir ".env"
$envDst = if ($OneFile) { Split-Path $outputExe } else { Join-Path $RootDir "dist\ledger" }
if (Test-Path $envSrc) {
    Copy-Item $envSrc (Join-Path $envDst ".env") -Force
    Write-Host "  Copied .env to output directory" -ForegroundColor Gray
}

# 复制 data 目录
$dataSrc = Join-Path $RootDir "data"
if (Test-Path $dataSrc) {
    $dataDst = Join-Path $envDst "data"
    if (-not (Test-Path $dataDst)) { New-Item -ItemType Directory -Path $dataDst -Force | Out-Null }
    Copy-Item "$dataSrc\*" $dataDst -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Copied data/ to output directory" -ForegroundColor Gray
}

# ─── 7. 完成提示 ─────────────────────────────────────

Write-Host "[6/6] Done!" -ForegroundColor Cyan
Write-Host ""
Write-Host "=" * 55
Write-Host "  Build Successful!"
Write-Host "=" * 55
Write-Host ""
Write-Host "  运行方式:" -ForegroundColor White
Write-Host "    双击 ledger.exe 即可打开桌面窗口"
Write-Host "    指定端口:  ledger.exe --port 8080"
Write-Host "    指定窗口:  ledger.exe --width 1400 --height 900"
Write-Host ""

if (-not $OneFile) {
    Write-Host "  分发步骤:" -ForegroundColor White
    Write-Host "    1. 将 dist/ledger/ 整个文件夹打 zip"
    Write-Host "    2. 用户解压后双击 ledger.exe"
    Write-Host "    3. 自动弹出桌面窗口，无需安装任何东西"
    Write-Host ""
}

Write-Host "  打包产物: $(Split-Path $outputExe)" -ForegroundColor Gray
Write-Host ""
