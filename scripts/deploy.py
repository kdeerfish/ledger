#!/usr/bin/env python3
"""
Ledger 打包发布脚本
用法: python scripts/deploy.py
"""

import os
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "deploy"


def log(msg, color="white"):
    colors = {
        "cyan": "\033[36m",
        "yellow": "\033[33m",
        "green": "\033[32m",
        "white": "\033[0m",
        "gray": "\033[90m",
    }
    c = colors.get(color, "")
    reset = "\033[0m" if c else ""
    print(f"{c}{msg}{reset}")


def clean_deploy():
    """清理 deploy 目录，保留 DEPLOY.md"""
    log("[1/4] 清理 deploy 目录...", "yellow")
    if not DEPLOY.exists():
        DEPLOY.mkdir(parents=True)
        log("  deploy 目录不存在，已创建", "green")
        return
    for item in DEPLOY.iterdir():
        if item.name == "DEPLOY.md":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    log("  已清理", "green")


def copy_service():
    """打包 ledger-service"""
    log("[2/4] 打包 ledger-service...", "yellow")
    svc = DEPLOY / "ledger-service"
    svc.mkdir(parents=True, exist_ok=True)

    # 复制 ledger_modules（排除 __pycache__）
    shutil.copytree(ROOT / "ledger_modules", svc / "ledger_modules",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # 复制 scripts（排除 __pycache__ 和打包脚本自身）
    shutil.copytree(ROOT / "scripts", svc / "scripts",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "deploy.py", "deploy.ps1"))

    # 复制配置文件
    shutil.copy2(ROOT / ".env.example", svc / ".env.example")

    log("  ledger-service 准备完成", "green")
    return svc


def copy_skills():
    """打包 ledger-skills"""
    log("[3/4] 打包 ledger-skills...", "yellow")
    skl = DEPLOY / "ledger-skills"
    skl.mkdir(parents=True, exist_ok=True)

    # 复制 scripts
    scripts_dir = skl / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "ledger-skills" / "scripts" / "ledger_cli.py",
                 scripts_dir / "ledger_cli.py")

    # 复制配置文件
    shutil.copy2(ROOT / "ledger-skills" / ".env.example", skl / ".env.example")
    shutil.copy2(ROOT / "ledger-skills" / "SKILL.md", skl / "SKILL.md")

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
    log("[4/4] 创建 zip 包...", "yellow")
    svc_zip = DEPLOY / "ledger-service.zip"
    skl_zip = DEPLOY / "ledger-skills.zip"

    make_zip(svc_dir, svc_zip)
    make_zip(skl_dir, skl_zip)

    log("  已创建 zip 包", "green")
    return svc_zip, skl_zip


def main():
    print()
    log("======================================", "cyan")
    log(" Ledger 打包发布", "cyan")
    log("======================================", "cyan")
    print()

    clean_deploy()
    svc_dir = copy_service()
    skl_dir = copy_skills()
    svc_zip, skl_zip = create_zips(svc_dir, skl_dir)

    # 输出结果
    print()
    log("======================================", "cyan")
    log(" 打包完成!", "green")
    log("======================================", "cyan")
    print()
    log("输出文件:", "white")
    log(f"  deploy\\ledger-service.zip  ({svc_zip.stat().st_size // 1024} KB)", "gray")
    log(f"  deploy\\ledger-skills.zip   ({skl_zip.stat().st_size // 1024} KB)", "gray")
    print()
    log("部署方法:", "white")
    log("  1. 上传 zip 到目标服务器", "gray")
    log("  2. 解压 ledger-service.zip 到 /volume1/docker/ledger/", "gray")
    log("  3. 解压 ledger-skills.zip 到 ~/.picoclaw/skills/ledger/", "gray")
    log("  4. 参考 deploy/DEPLOY.md 进行配置", "gray")


if __name__ == "__main__":
    main()
