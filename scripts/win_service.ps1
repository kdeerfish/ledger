<# 
.SYNOPSIS
    Ledger Windows 服务安装/卸载脚本
.DESCRIPTION
    使用 NSSM (Non-Sucking Service Manager) 将 Ledger 注册为 Windows 系统服务
    支持开机自启、自动重启、日志记录
.NOTES
    需要管理员权限运行
    NSSM 下载: https://nssm.cc/download
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("install", "uninstall", "start", "stop", "restart", "status")]
    [string]$Action,

    [string]$ServiceName = "LedgerWeb",
    [string]$DisplayName = "Ledger Personal Finance Web Service",
    [string]$Description = "Ledger 记账系统 Web 服务 - 默认端口 5800",

    [string]$ExePath = "",           # ledger.exe 路径，默认当前目录下
    [string]$Host_ = "0.0.0.0",      # 绑定地址
    [int]$Port = 5800,               # 端口
    [string]$WorkDir = "",           # 工作目录，默认 exe 所在目录

    [string]$NSSMPath = "nssm",      # nssm 可执行文件路径
    [string]$LogDir = ""             # 日志目录，默认 exe 同级 logs/
)

$ErrorActionPreference = "Stop"

# ─── 辅助函数 ──────────────────────────────────────────

function Write-Header($msg) {
    Write-Host ""
    Write-Host "=" * 50
    Write-Host " $msg"
    Write-Host "=" * 50
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-NSSM {
    # 检查多个可能的 NSSM 位置
    $searchPaths = @(
        $NSSMPath,
        ".\tools\nssm.exe",
        ".\nssm.exe",
        "$env:ProgramFiles\nssm\win64\nssm.exe",
        "$env:ProgramFiles\nssm\win32\nssm.exe",
        "$env:ChocolateyInstall\tools\nssm.exe"
    )
    foreach ($p in $searchPaths) {
        $resolved = Get-Command $p -ErrorAction SilentlyContinue
        if ($resolved) {
            return $resolved.Source
        }
    }
    # 尝试直接执行
    try { & nssm version 2>$null; return "nssm" } catch {}
    return $null
}

# ─── 解析路径 ──────────────────────────────────────────

if (-not (Test-Admin)) {
    Write-Host "[ERROR] 需要管理员权限！请右键 '以管理员身份运行'" -ForegroundColor Red
    exit 1
}

$nssm = Find-NSSM
if (-not $nssm) {
    Write-Host "[ERROR] 未找到 NSSM！" -ForegroundColor Red
    Write-Host ""
    Write-Host "请下载 NSSM: https://nssm.cc/download"
    Write-Host "解压后将 nssm.exe 放到以下位置之一:"
    Write-Host "  - 项目目录/tools/nssm.exe"
    Write-Host "  - 或指定 -NSSMPath 参数"
    exit 1
}

Write-Host "Using NSSM: $nssm" -ForegroundColor Gray

# exe 路径
if (-not $ExePath) {
    $ExePath = Join-Path $PSScriptRoot "..\dist\ledger\ledger.exe"
    if (-not (Test-Path $ExePath)) {
        $ExePath = Join-Path $PSScriptRoot "..\ledger.exe"
    }
}
$ExePath = Resolve-Path $ExePath -ErrorAction SilentlyContinue
if (-not $ExePath -or -not (Test-Path $ExePath)) {
    Write-Host "[ERROR] 未找到 ledger.exe: $ExePath" -ForegroundColor Red
    Write-Host "请先打包: pyinstaller ledger.spec" -ForegroundColor Yellow
    exit 1
}
$ExePath = $ExePath.Path

# 工作目录
if (-not $WorkDir) {
    $WorkDir = Split-Path $ExePath -Parent
}

# 日志目录
if (-not $LogDir) {
    $LogDir = Join-Path $WorkDir "logs"
}
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$stdoutLog = Join-Path $LogDir "ledger-stdout.log"
$stderrLog = Join-Path $LogDir "ledger-stderr.log"

Write-Host "  Exe:     $ExePath"
Write-Host "  WorkDir: $WorkDir"
Write-Host "  Logs:    $LogDir"
Write-Host "  Address: http://${Host_}:${Port}"

# ─── 操作 ──────────────────────────────────────────

switch ($Action) {
    "install" {
        Write-Header "安装 Windows 服务: $ServiceName"

        # 先卸载旧的
        & $nssm stop $ServiceName 2>$null
        & $nssm remove $ServiceName confirm 2>$null

        # 安装服务
        & $nssm install $ServiceName $ExePath
        & $nssm set $ServiceName DisplayName $DisplayName
        & $nssm set $ServiceName Description $Description
        & $nssm set $ServiceName AppDirectory $WorkDir

        # 启动参数
        $appArgs = "--host $Host_ --port $Port"
        & $nssm set $ServiceName AppParameters $appArgs

        # 日志
        & $nssm set $ServiceName AppStdout $stdoutLog
        & $nssm set $ServiceName AppStderr $stderrLog
        & $nssm set $ServiceName AppStdoutCreationDisposition 4  # Append
        & $nssm set $ServiceName AppStderrCreationDisposition 4
        & $nssm set $ServiceName AppRotateFiles 1
        & $nssm set $ServiceName AppRotateBytes 10485760  # 10MB 自动轮转

        # 开机自启 & 自动重启
        & $nssm set $ServiceName Start SERVICE_AUTO_START
        & $nssm set $ServiceName AppExit Default Restart
        & $nssm set $ServiceName AppRestartDelay 5000  # 崩溃后 5 秒重启

        # 环境变量（传递 .env 给服务进程）
        & $nssm set $ServiceName AppEnvironmentExtra "PYTHONUTF8=1"

        # 恢复策略
        & $nssm set $ServiceName AppRestartDelay 5000
        & $nssm set $ServiceName FailureActionsOnNonCrashFailures 1

        # 启动服务
        & $nssm start $ServiceName

        Write-Host ""
        Write-Host "[OK] 服务安装并启动成功！" -ForegroundColor Green
        Write-Host "  服务名: $ServiceName"
        Write-Host "  地址:   http://${Host_}:${Port}"
        Write-Host "  日志:   $LogDir"
        Write-Host ""
        Write-Host "管理命令:" -ForegroundColor Cyan
        Write-Host "  .\scripts\win_service.ps1 -Action stop"
        Write-Host "  .\scripts\win_service.ps1 -Action start"
        Write-Host "  .\scripts\win_service.ps1 -Action uninstall"
        Write-Host "  或在 services.msc 中查找 '$DisplayName'"
    }

    "uninstall" {
        Write-Header "卸载 Windows 服务: $ServiceName"
        & $nssm stop $ServiceName 2>$null
        & $nssm remove $ServiceName confirm
        Write-Host "[OK] 服务已卸载" -ForegroundColor Green
    }

    "start" {
        Write-Host "启动服务 $ServiceName ..."
        & $nssm start $ServiceName
        Write-Host "[OK] 服务已启动" -ForegroundColor Green
    }

    "stop" {
        Write-Host "停止服务 $ServiceName ..."
        & $nssm stop $ServiceName
        Write-Host "[OK] 服务已停止" -ForegroundColor Green
    }

    "restart" {
        Write-Host "重启服务 $ServiceName ..."
        & $nssm restart $ServiceName
        Write-Host "[OK] 服务已重启" -ForegroundColor Green
    }

    "status" {
        Write-Header "服务状态: $ServiceName"
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            Write-Host "  状态:   $($svc.Status)"
            Write-Host "  启动:   $($svc.StartType)"
            Write-Host "  显示名: $($svc.DisplayName)"
        } else {
            Write-Host "  服务未安装" -ForegroundColor Yellow
        }
    }
}
