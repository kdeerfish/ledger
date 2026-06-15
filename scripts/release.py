#!/usr/bin/env python3
"""
Ledger 自动发布脚本
用法:
  python scripts/release.py                # 交互式，自动从 pyproject.toml 读版本
  python scripts/release.py 1.0.0          # 指定版本号
  python scripts/release.py --dry-run      # 只打包，不发布
  python scripts/release.py --skip-tests   # 跳过测试
"""

import argparse
import json
import subprocess
import sys
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        import re

        def _read_version(path: Path) -> str:
            text = path.read_text(encoding="utf-8")
            m = re.search(r'^version\s*=\s*"(.+?)"', text, re.MULTILINE)
            return m.group(1) if m else "0.0.0"

        tomllib = None  # type: ignore
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "deploy"

# Gitea 配置（可通过环境变量覆盖）
# 格式: http://192.168.31.126:8818
GITEA_URL = __import__("os").environ.get("GITEA_URL", "http://192.168.31.126:8818")
GITEA_TOKEN = __import__("os").environ.get("GITEA_TOKEN", "")
REPO_OWNER = "zouzhenglu"
REPO_NAME = "ledger"


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


def run(cmd, check=True):
    """执行 shell 命令"""
    log(f"  $ {cmd}", "gray")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT)
    if result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            log(f"    {line}", "gray")
    if result.returncode != 0 and check:
        if result.stderr.strip():
            for line in result.stderr.strip().split("\n"):
                log(f"  {line}", "red")
        log(f"  命令失败 (exit {result.returncode})", "red")
        sys.exit(1)
    return result


def get_version():
    """从 pyproject.toml 读取版本号"""
    if tomllib is not None:
        with open(ROOT / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    else:
        return _read_version(ROOT / "pyproject.toml")


def run_tests():
    """运行测试"""
    log("[1/6] 运行测试...", "yellow")
    result = run("python -m pytest tests -v --tb=short -q", check=False)
    if result.returncode != 0:
        log("  测试未通过，是否继续？(y/N)", "yellow")
        if input("  > ").strip().lower() != "y":
            sys.exit(1)
    else:
        log("  测试通过 ✓", "green")


def build_deploy():
    """运行打包脚本"""
    log("[2/6] 打包...", "yellow")
    run("python scripts/deploy.py")
    log("  打包完成 ✓", "green")


def git_tag_and_push(version):
    """创建 git tag 并推送"""
    tag = f"v{version}"
    log(f"[3/6] 创建 git tag: {tag}", "yellow")

    # 检查 tag 是否已存在
    result = run(f"git tag -l {tag}", check=False)
    if tag in result.stdout.strip():
        log(f"  tag {tag} 已存在，跳过创建", "gray")
    else:
        run(f'git tag -a {tag} -m "Release {tag}"')

    log(f"[4/6] 推送 tag 到 origin...", "yellow")
    run(f"git push origin {tag}")
    log(f"  tag 已推送 ✓", "green")


def gitea_request(method, path, data=None, files=None):
    """调用 Gitea API"""
    url = f"{GITEA_URL}/api/v1{path}"
    log(f"  API: {method} {url}", "gray")

    if files:
        # multipart/form-data 上传文件
        boundary = "----LedgerReleaseBoundary"
        body = b""
        for key, value in (data or {}).items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += f"{value}\r\n".encode()
        for field_name, file_path in files.items():
            filename = Path(file_path).name
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
            body += b"Content-Type: application/zip\r\n\r\n"
            body += Path(file_path).read_bytes()
            body += b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        content_type = f"multipart/form-data; boundary={boundary}"
    elif data:
        body = json.dumps(data).encode("utf-8")
        content_type = "application/json"
    else:
        body = None
        content_type = "application/json"

    headers = {
        "Content-Type": content_type,
        "Accept": "application/json",
    }
    if GITEA_TOKEN:
        headers["Authorization"] = f"token {GITEA_TOKEN}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        log(f"  API 错误 ({e.code}): {error_body}", "red")
        sys.exit(1)


def create_gitea_release(version, tag):
    """通过 Gitea API 创建 Release 并上传附件"""
    log("[5/6] 创建 Gitea Release...", "yellow")

    # 先检查 release 是否已存在
    releases = gitea_request("GET", f"/repos/{REPO_OWNER}/{REPO_NAME}/releases")
    for r in releases:
        if r.get("tag_name") == tag:
            log(f"  Release {tag} 已存在，跳过创建", "gray")
            return r

    release_data = {
        "tag_name": tag,
        "name": f"Release {tag}",
        "body": f"## {tag}\n\n### 发布内容\n\n- `ledger-service.zip` 核心服务\n- `ledger-skills.zip` AI Agent 技能\n\n### 部署\n\n参考 `deploy/DEPLOY.md`",
        "draft": False,
        "prerelease": False,
    }
    release = gitea_request("POST", f"/repos/{REPO_OWNER}/{REPO_NAME}/releases", data=release_data)
    release_id = release["id"]
    log(f"  Release 已创建 (id={release_id}) ✓", "green")

    # 上传附件
    log("[6/6] 上传附件...", "yellow")
    zip_files = list(DEPLOY.glob("*.zip"))
    for zip_path in zip_files:
        log(f"  上传 {zip_path.name}...", "gray")
        gitea_request(
            "POST",
            f"/repos/{REPO_OWNER}/{REPO_NAME}/releases/{release_id}/assets",
            files={"attachment": str(zip_path)},
        )
        log(f"  {zip_path.name} ✓", "green")

    return release


def main():
    parser = argparse.ArgumentParser(description="Ledger 自动发布")
    parser.add_argument("version", nargs="?", help="版本号 (默认从 pyproject.toml 读取)")
    parser.add_argument("--dry-run", action="store_true", help="只打包，不发布到 Gitea")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试")
    parser.add_argument("--skip-git", action="store_true", help="跳过 git tag")
    args = parser.parse_args()

    version = args.version or get_version()
    tag = f"v{version}"

    print()
    log("======================================", "cyan")
    log(f" Ledger Release {tag}", "cyan")
    log("======================================", "cyan")
    print()

    # Step 1: 测试
    if not args.skip_tests:
        run_tests()
    else:
        log("[1/6] 跳过测试", "gray")

    # Step 2: 打包
    build_deploy()

    # Step 3-4: Git tag
    if not args.skip_git:
        git_tag_and_push(version)
    else:
        log("[3/6] 跳过 git tag", "gray")
        log("[4/6] 跳过 git push", "gray")

    # Step 5-6: Gitea Release
    if not args.dry_run:
        if not GITEA_TOKEN:
            log("", "white")
            log("未设置 GITEA_TOKEN 环境变量，跳过 Gitea Release 创建", "yellow")
            log("设置方法:", "gray")
            log('  $env:GITEA_TOKEN = "your-token-here"', "gray")
            log("然后重新运行此脚本", "gray")
            log("", "white")
            log("已创建的 git tag 可手动创建 Release:", "gray")
            log(f"  {GITEA_URL}/{REPO_OWNER}/{REPO_NAME}/releases/new?tag={tag}", "gray")
        else:
            release = create_gitea_release(version, tag)
            log("", "white")
            log("Release 页面:", "cyan")
            log(f"  {GITEA_URL}/{REPO_OWNER}/{REPO_NAME}/releases/tag/{tag}", "cyan")
    else:
        log("[5/6] 跳过 Gitea Release (--dry-run)", "gray")
        log("[6/6] 跳过附件上传 (--dry-run)", "gray")

    # 输出结果
    print()
    log("======================================", "cyan")
    log(f" Release {tag} 完成!", "green")
    log("======================================", "cyan")
    print()
    log("部署命令:", "white")
    log(f"  scp deploy/ledger-service.zip user@nas:/volume1/docker/ledger/", "gray")
    log(f"  scp deploy/ledger-skills.zip user@nas:/volume1/docker/ledger/", "gray")
    log(f"  # 解压后参考 deploy/DEPLOY.md 配置", "gray")


if __name__ == "__main__":
    main()
