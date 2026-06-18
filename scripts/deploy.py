#!/usr/bin/env python3
"""
Ledger 打包发布脚本
用法: python scripts/deploy.py

打包内容:
  - ledger-service.zip  核心服务（Python 后端 + 构建好的 React 前端 + Dockerfile）
  - ledger-skills.zip   AI Agent 技能
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "deploy"


def log(msg, color="white"):
    colors = {
        "cyan": "\033[36m",
        "yellow": "\033[33m",
        "green": "\033[32m",
        "red": "\033[31m",
        "white": "\033[0m",
        "gray": "\033[90m",
    }
    c = colors.get(color, "")
    reset = "\033[0m" if c else ""
    print(f"{c}{msg}{reset}")


def run(cmd, cwd=None):
    log(f"  $ {cmd}", "gray")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or ROOT)
    if result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            log(f"    {line}", "gray")
    if result.returncode != 0:
        if result.stderr.strip():
            for line in result.stderr.strip().split("\n"):
                log(f"  {line}", "red")
        log(f"  命令失败 (exit {result.returncode})", "red")
        raise SystemExit(1)
    return result


def build_frontend():
    """构建 React 前端到 frontend/dist/"""
    log("[前置] 构建 React 前端...", "yellow")
    frontend_dir = ROOT / "frontend"
    if frontend_dir.exists():
        run("npm install", cwd=frontend_dir)
        run("npm run build", cwd=frontend_dir)
        log("  前端构建完成 ✓", "green")
    else:
        log("  frontend/ 目录不存在，跳过前端构建", "yellow")


def clean_deploy():
    """清理 deploy 目录"""
    log("[1/5] 清理 deploy 目录...", "yellow")
    if not DEPLOY.exists():
        DEPLOY.mkdir(parents=True)
    else:
        for item in DEPLOY.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    # 从项目根目录复制 DEPLOY.md
    src_md = ROOT / "DEPLOY.md"
    if src_md.exists():
        shutil.copy2(src_md, DEPLOY / "DEPLOY.md")
    log("  已清理", "green")


def copy_service():
    """打包 ledger-service（Python 后端 + 前端构建产物 + Dockerfile）"""
    log("[2/5] 打包 ledger-service...", "yellow")
    svc = DEPLOY / "ledger-service"
    svc.mkdir(parents=True, exist_ok=True)

    # 复制 ledger_modules（排除 __pycache__）
    shutil.copytree(ROOT / "ledger_modules", svc / "ledger_modules",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # 复制 scripts（排除自身）
    shutil.copytree(ROOT / "scripts", svc / "scripts",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "deploy.py"))

    # 复制 web 目录
    shutil.copytree(ROOT / "web", svc / "web",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # 复制构建好的前端
    dist_dir = ROOT / "frontend" / "dist"
    if dist_dir.exists():
        shutil.copytree(dist_dir, svc / "frontend" / "dist")
        log("  前端构建产物已纳入 ✓", "green")

    # 复制配置文件
    shutil.copy2(ROOT / "requirements.txt", svc / "requirements.txt")
    shutil.copy2(ROOT / "pyproject.toml", svc / "pyproject.toml")
    shutil.copy2(ROOT / "Dockerfile", svc / "Dockerfile")
    shutil.copy2(ROOT / "docker-compose.yml", svc / "docker-compose.yml")
    if (ROOT / ".env.example").exists():
        shutil.copy2(ROOT / ".env.example", svc / ".env.example")

    log("  ledger-service 准备完成", "green")
    return svc


def copy_skills():
    """打包 ledger-skills"""
    log("[3/5] 打包 ledger-skills...", "yellow")
    skl = DEPLOY / "ledger-skills"
    skl.mkdir(parents=True, exist_ok=True)

    src = ROOT / "skills" / "ledger"
    if not src.exists():
        log("  skills/ledger 目录不存在，跳过", "yellow")
        return skl

    # 复制 scripts
    scripts_dir = skl / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    shutil.copy2(src / "scripts" / "ledger_cli.py", scripts_dir / "ledger_cli.py")

    # 复制 SKILL.md 和配置文件
    shutil.copy2(src / ".env.example", skl / ".env.example")
    shutil.copy2(src / "SKILL.md", skl / "SKILL.md")

    # 复制 references/
    refs_src = src / "references"
    if refs_src.exists():
        shutil.copytree(refs_src, skl / "references")

    # 复制 examples/
    ex_src = src / "examples"
    if ex_src.exists():
        shutil.copytree(ex_src, skl / "examples")

    log("  ledger-skills 准备完成", "green")
    return skl


def make_zip(src_dir, zip_path):
    """将目录打包为 zip"""
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in src_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(src_dir))


def create_zips(svc_dir, skl_dir):
    """创建 zip 包"""
    log("[4/5] 创建 zip 包...", "yellow")
    svc_zip = DEPLOY / "ledger-service.zip"
    skl_zip = DEPLOY / "ledger-skills.zip"

    # service zip 加上 DEPLOY.md
    deploy_md = DEPLOY / "DEPLOY.md"
    make_zip(svc_dir, svc_zip)
    if deploy_md.exists():
        with zipfile.ZipFile(svc_zip, "a", zipfile.ZIP_DEFLATED) as zf:
            zf.write(deploy_md, "DEPLOY.md")

    make_zip(skl_dir, skl_zip)
    log("  已创建 zip 包", "green")
    return svc_zip, skl_zip


def show_result(svc_zip, skl_zip):
    """输出结果"""
    log("[5/5] 输出结果", "yellow")
    print()
    log("  ═══════════════════════════════════════", "cyan")
    log("  打包完成!", "green")
    log("  ═══════════════════════════════════════", "cyan")
    print()
    log(f"  📦 {svc_zip.name}  ({svc_zip.stat().st_size // 1024} KB)", "white")
    log(f"  📦 {skl_zip.name}   ({skl_zip.stat().st_size // 1024} KB)", "white")
    print()
    log("  部署方法:", "white")
    log("    Docker:   docker compose up -d --build", "gray")
    log("    手动:     解压 ledger-service.zip → python web/run.py", "gray")
    print()


def main():
    print()
    log("╔═══════════════════════════════════════╗", "cyan")
    log("║     Ledger 打包发布", "cyan")
    log("╚═══════════════════════════════════════╝", "cyan")
    print()

    build_frontend()
    clean_deploy()
    svc_dir = copy_service()
    skl_dir = copy_skills()
    svc_zip, skl_zip = create_zips(svc_dir, skl_dir)
    show_result(svc_zip, skl_zip)


if __name__ == "__main__":
    main()
