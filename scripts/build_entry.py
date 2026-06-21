#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger 打包入口 - PyInstaller 使用
双击 exe 时默认启动桌面模式，加 --service 则纯服务模式
"""

import os
import sys
import argparse
import signal

# ─── PyInstaller 路径兼容 ──────────────────────────────
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = os.path.dirname(sys.executable)
    MEIPASS_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEIPASS_DIR = BUNDLE_DIR

sys.path.insert(0, MEIPASS_DIR)

# 修复 Windows 编码问题
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    os.environ['PYTHONUTF8'] = '1'

# ─── 加载配置 ──────────────────────────────────────
os.environ.setdefault('LEDGER_PATH', BUNDLE_DIR)
from ledger_modules import desktop_config
desktop_config.load()
_cfg = desktop_config.get

if not _cfg('db_path'):
    default_db = os.path.join(BUNDLE_DIR, 'data', 'ledger.db')
    os.environ.setdefault('LEDGER_DB_PATH', default_db)
else:
    os.environ['LEDGER_DB_PATH'] = _cfg('db_path')

# 加载 .env
env_file = os.path.join(BUNDLE_DIR, '.env')
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value

from web.app import app, WEB_HOST, WEB_PORT, WEB_DEBUG, DB_PATH


def _println(s=""):
    try:
        sys.stdout.write(s + "\n")
    except UnicodeEncodeError:
        sys.stdout.write(s.encode("ascii", "replace").decode("ascii") + "\n")


def _find_free_port(start=5800, end=5900):
    import socket
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return start


def main():
    parser = argparse.ArgumentParser(description='Ledger - Personal Finance Manager')
    parser.add_argument('--service', action='store_true',
                        help='服务模式：仅运行 Flask，不显示窗口')
    parser.add_argument('--host', default=None, help='绑定地址')
    parser.add_argument('--port', type=int, default=None, help='端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    args = parser.parse_args()

    # 服务模式
    if args.service or _cfg('service_mode'):
        host = args.host or _cfg('service_host') or '0.0.0.0'
        port = args.port or _cfg('port') or WEB_PORT
        debug = args.debug or WEB_DEBUG

        _println("=" * 50)
        _println("  Ledger - Service Mode")
        _println("=" * 50)
        _println(f"  Database: {DB_PATH}")
        _println(f"  Address:  http://{host}:{port}")
        _println("  Press Ctrl+C to stop")
        _println("=" * 50)

        def _shutdown(sig, frame):
            _println("\n[INFO] Shutting down...")
            sys.exit(0)
        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        app.run(host=host, port=port, debug=debug, use_reloader=False)
        return

    # 桌面模式：委托给 desktop_entry.py
    from scripts.desktop_entry import run_desktop_mode, run_desktop_mode
    host = args.host or WEB_HOST
    port = args.port or _cfg('port') or WEB_PORT
    if _cfg('auto_port') and not args.port:
        port = _find_free_port()
    debug = args.debug or WEB_DEBUG

    run_desktop_mode(port, _cfg('window_width'), _cfg('window_height'), debug)


if __name__ == '__main__':
    main()
