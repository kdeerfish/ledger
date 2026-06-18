#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger Web 服务启动器
一键启动 Web 界面，适配飞牛OS (FnOS) 及任何 Linux/Windows 环境

用法：
    python web/run.py              # 启动 Web 服务（默认 5000 端口）
    python web/run.py --port 8080  # 指定端口
    python web/run.py --host 0.0.0.0 --port 5000
"""

import os
import sys
import argparse

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# 导入并启动 Web 应用
from web.app import app, WEB_HOST, WEB_PORT, WEB_DEBUG, DB_PATH


def _println(s=""):
    """安全打印（处理 Windows GBK 编码问题）"""
    out = sys.stdout
    try:
        out.write(s + "\n")
    except UnicodeEncodeError:
        out.write(s.encode("ascii", "replace").decode("ascii") + "\n")


def main():
    parser = argparse.ArgumentParser(description='Ledger Web Service Starter')
    parser.add_argument('--host', default=None, help='Bind address (default 0.0.0.0)')
    parser.add_argument('--port', type=int, default=None, help='Port (default 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    host = args.host or WEB_HOST
    port = args.port or WEB_PORT
    debug = args.debug or WEB_DEBUG

    _println("=" * 50)
    _println(" Ledger - Web Interface")
    _println("=" * 50)
    _println("  Database: " + str(DB_PATH))
    _println("  Address:  http://{}:{}".format(host, port))
    _println("")
    _println("  FnOS Usage:")
    _println("     1. Run this script on your NAS")
    _println("     2. Open http://NAS_IP:{} in browser".format(port))
    _println("     3. Press Ctrl+C to stop")
    _println("")
    _println("  Run in background (Linux):")
    _println("     nohup python web/run.py > ledger-web.log 2>&1 &")
    _println("     screen -dmS ledger python web/run.py")
    _println("=" * 50)
    _println("")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
