#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger 全自动测试脚本
一键完成：启动服务 → 检测 API → 停止服务

用法：
    python scripts/auto_test.py
    python scripts/auto_test.py --port 5800
    python scripts/auto_test.py --skip-api    # 只测单元测试
    python scripts/auto_test.py --skip-unit   # 只测 API
"""

import argparse
import contextlib
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from io import StringIO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 5800
SERVER_PROCESS = None


def _print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))


def start_server(port):
    """启动 Flask 服务，返回进程对象"""
    global SERVER_PROCESS
    env = os.environ.copy()
    env['WEB_PORT'] = str(port)
    env['WEB_HOST'] = '127.0.0.1'
    env['WEB_DEBUG'] = 'false'

    _print(f'[1/3] 启动 Web 服务 (127.0.0.1:{port}) ...')

    SERVER_PROCESS = subprocess.Popen(
        [sys.executable, '-c', f'''
import sys
sys.path.insert(0, {repr(ROOT)})
import web.app as app_mod
app_mod.app.run(host='127.0.0.1', port={port}, debug=False)
'''],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        cwd=ROOT
    )

    # 等待服务就绪（最多 15 秒）
    for i in range(30):
        time.sleep(0.5)
        try:
            r = urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=2)
            if r.status == 200:
                _print(f'  [OK] 服务已启动')
                return True
        except Exception:
            continue

    _print(f'  [FAIL] 服务启动超时')
    # 读取子进程的 stderr 输出，帮助诊断
    try:
        stderr_out = SERVER_PROCESS.stderr.read().decode('utf-8', errors='replace')
        if stderr_out.strip():
            _print(f'  [STDERR] {stderr_out[:1000]}')
    except Exception:
        pass
    return False


def stop_server():
    """停止服务"""
    global SERVER_PROCESS
    if SERVER_PROCESS:
        _print('  停止服务...')
        if sys.platform == 'win32':
            SERVER_PROCESS.kill()
        else:
            os.kill(SERVER_PROCESS.pid, signal.SIGTERM)
        SERVER_PROCESS.wait(timeout=5)
        SERVER_PROCESS = None
        _print('  [OK] 已停止')


def run_api_test(port):
    """运行 API 手动测试"""
    _print(f'\n[2/3] API 接口测试 (port {port}) ...\n')

    # 导入并执行 test_api 的测试逻辑
    sys.path.insert(0, os.path.join(ROOT, 'scripts'))
    import importlib.util
    spec = importlib.util.spec_from_file_location('test_api',
        os.path.join(ROOT, 'scripts', 'test_api.py'))
    test_api = importlib.util.module_from_spec(spec)
    # 不运行 main，直接调 test()
    spec.loader.exec_module(test_api)

    api_url = f'http://127.0.0.1:{port}'
    success = test_api.test(api_url)
    return success


def run_unit_tests():
    """运行 pytest 单元测试（直接调用 pytest.main 避免子进程环境问题）"""
    _print(f'\n[3/3] 单元测试 (pytest) ...\n')
    try:
        import pytest
    except ImportError:
        _print('  [FAIL] 找不到 pytest (未安装或不在当前 Python 环境)')
        return False, ''

    stdout_capture = StringIO()
    stderr_capture = StringIO()
    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exit_code = pytest.main(['tests', '-v', '--tb=short'])
    except SystemExit:
        exit_code = 1

    stdout = stdout_capture.getvalue()
    stderr = stderr_capture.getvalue()

    _print(stdout[-3000:] if len(stdout) > 3000 else stdout)
    if stderr:
        _print(f'  [STDERR] {stderr[:500]}')

    passed = 'passed' in stdout and 'failed' not in stdout
    return passed, stdout


def main():
    parser = argparse.ArgumentParser(description='Ledger 全自动测试')
    parser.add_argument('--port', type=int, default=PORT, help='端口')
    parser.add_argument('--skip-api', action='store_true', help='跳过 API 测试')
    parser.add_argument('--skip-unit', action='store_true', help='跳过单元测试')
    args = parser.parse_args()

    port = args.port
    all_ok = True

    _print('=' * 50)
    _print('Ledger 全自动测试')
    _print('=' * 50)

    if not args.skip_api:
        if not start_server(port):
            all_ok = False
        else:
            time.sleep(1)  # 等一秒稳定
            if not run_api_test(port):
                all_ok = False
            stop_server()
    else:
        _print('[1/3] 跳过 API 测试')

    if not args.skip_unit:
        passed, output = run_unit_tests()
        if not passed:
            all_ok = False
    else:
        _print('[3/3] 跳过单元测试')

    _print('\n' + '=' * 50)
    if all_ok:
        _print('全部测试通过!')
    else:
        _print('有测试失败，请检查上面的输出')

    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
