#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger 桌面入口 - Flask 服务 + 系统托盘 + 浏览器

启动流程:
  1. 双击 exe → 启动 Flask 后台 + 系统托盘 + 自动打开浏览器
  2. 第二次双击 → 检测到已运行，用浏览器打开新标签
  3. 托盘右键 → 打开主界面 / 设置 / 退出
"""

import os
import sys
import time
import signal
import threading
import webbrowser

# ─── PyInstaller 路径兼容 ──────────────────────────────
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = os.path.dirname(sys.executable)
    MEIPASS_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEIPASS_DIR = BUNDLE_DIR

sys.path.insert(0, MEIPASS_DIR)

# 修复 Windows 编码问题 & console=False 时 stdout/stderr 为 None 的问题
if sys.platform == 'win32':
    try:
        if sys.stdout is not None:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        else:
            sys.stdout = open(os.devnull, 'w', encoding='utf-8')
        if sys.stderr is not None:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        else:
            sys.stderr = open(os.devnull, 'w', encoding='utf-8')
    except Exception:
        pass
    os.environ['PYTHONUTF8'] = '1'

# ─── 加载配置 ──────────────────────────────────────
os.environ.setdefault('LEDGER_PATH', BUNDLE_DIR)
from ledger_modules import desktop_config
desktop_config.load()
_cfg = desktop_config.get

# 配置文件中的默认路径
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


# ─── 单实例检查 ────────────────────────────────────

LOCK_FILE = os.path.join(BUNDLE_DIR, '.ledger.pid')
SIGNAL_FILE = os.path.join(BUNDLE_DIR, '.ledger.signal')


def _is_pid_alive(pid):
    """检查进程是否存活"""
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
        except Exception:
            pass
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _try_signal_existing():
    """尝试唤醒已运行的实例，返回 True 表示有实例在运行"""
    if not os.path.exists(LOCK_FILE):
        return False
    try:
        with open(LOCK_FILE, 'r') as f:
            old_pid = int(f.read().strip())
    except (ValueError, IOError):
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass
        return False

    if old_pid == os.getpid():
        return False  # 自身

    if _is_pid_alive(old_pid):
        # 实例在运行，写入信号文件通知它打开浏览器
        try:
            with open(SIGNAL_FILE, 'w') as f:
                f.write(str(os.getpid()))
            _println(f"[INFO] Ledger 已在运行 (PID {old_pid})，正在打开浏览器...")
        except IOError:
            pass
        return True
    else:
        # 旧进程已死，清理锁文件
        try:
            os.remove(LOCK_FILE)
        except OSError:
            pass
        return False


def _acquire_lock():
    """获取单实例锁，返回 True 表示成功"""
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except IOError:
        return False


def _release_lock():
    """释放锁文件"""
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                os.remove(LOCK_FILE)
    except (ValueError, IOError, OSError):
        pass


def _check_signal_file():
    """检查信号文件，如果有就清除并返回 True"""
    if os.path.exists(SIGNAL_FILE):
        try:
            os.remove(SIGNAL_FILE)
            return True
        except OSError:
            pass
    return False


def _get_version():
    try:
        import tomllib
        pyproject = os.path.join(MEIPASS_DIR, 'pyproject.toml')
        with open(pyproject, 'rb') as f:
            return 'v' + tomllib.load(f).get('project', {}).get('version', '0.0.0')
    except Exception:
        return 'v0.0.0'


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


def _println(s=""):
    try:
        out = sys.stdout
        if out is None:
            return
        out.write(s + "\n")
    except (AttributeError, UnicodeEncodeError):
        try:
            out.write(s.encode("ascii", "replace").decode("ascii") + "\n")
        except Exception:
            pass


# ─── Flask 后台线程 ────────────────────────────────────

_flask_server = None
_flask_ready = threading.Event()


def run_flask(host, port):
    global _flask_server
    from web.app import app
    from werkzeug.serving import make_server

    _flask_server = make_server(host, port, app, threaded=True)
    _flask_ready.set()
    _flask_server.serve_forever()


def shutdown_flask():
    global _flask_server
    if _flask_server:
        _flask_server.shutdown()
        _flask_server = None


# ─── 系统托盘 ──────────────────────────────────────

_tray = None
_tray_ready = threading.Event()


def _create_tray_icon():
    """创建系统托盘图标"""
    global _tray, _tray_ready

    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        _tray_ready.set()
        return

    def make_icon():
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([4, 4, 60, 60], fill=(9, 132, 227, 255))
        draw.text((18, 14), "L", fill=(255, 255, 255, 255))
        return image

    def on_open_ui(icon, item):
        webbrowser.open(f'http://127.0.0.1:{_port}')

    def on_open_settings(icon, item):
        webbrowser.open(f'http://127.0.0.1:{_port}/settings')

    def on_exit(icon, item):
        icon.stop()
        shutdown_flask()
        _release_lock()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem('打开主界面', on_open_ui, default=True),
        pystray.MenuItem('设置', on_open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('退出', on_exit),
    )

    def _setup_visible(icon):
        try:
            icon.visible = True
        except Exception:
            pass
        try:
            icon.notify("Ledger 已启动", "右键此图标可打开界面或退出。")
        except Exception:
            pass
        _promote_tray_icon()

    _tray = pystray.Icon(
        name='ledger_desktop',
        icon=make_icon(),
        title=f'Ledger {_get_version()}',
        menu=menu,
    )
    _tray_ready.set()

    try:
        _tray.run(setup=_setup_visible)
    except Exception:
        pass


def start_tray():
    """在后台线程启动托盘"""
    t = threading.Thread(target=_create_tray_icon, daemon=True)
    t.start()
    _tray_ready.wait(timeout=5)


def update_tray_tooltip(text):
    """更新托盘提示文字"""
    if _tray:
        try:
            _tray.title = text
        except Exception:
            pass


# ─── Windows 原生通知 + 全局快捷键 ──────────────────────

def _start_global_hotkey():
    """注册全局快捷键 Ctrl+Shift+L 打开浏览器（仅 Windows）"""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        HOTKEY_ID = 1
        MOD_CONTROL = 0x0002
        MOD_SHIFT = 0x0004
        VK_L = 0x4C

        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_L):
            return

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                webbrowser.open(f'http://127.0.0.1:{_port}')
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception:
        pass
    finally:
        try:
            import ctypes
            ctypes.windll.user32.UnregisterHotKey(None, 1)
        except Exception:
            pass


def _promote_tray_icon():
    """让 Windows 11 在任务栏显示托盘图标（不藏到溢出区）"""
    if sys.platform != 'win32':
        return
    try:
        import winreg
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        base_key = r"Control Panel\NotifyIconSettings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base_key) as key:
            i = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(key, i)
                    sub_path = f"{base_key}\\{sub_name}"
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as sub:
                        try:
                            val, _ = winreg.QueryValueEx(sub, "ExecutablePath")
                            if val and os.path.normcase(os.path.normpath(val)) == os.path.normcase(os.path.normpath(exe_path)):
                                winreg.SetValueEx(sub, "IsPromoted", 0, winreg.REG_DWORD, 1)
                                return
                        except FileNotFoundError:
                            pass
                    i += 1
                except OSError:
                    break
    except Exception:
        pass


# ─── 主入口 ────────────────────────────────────────

_port = 5800  # 全局端口，供托盘和快捷键回调使用


def main():
    global _port

    import argparse
    parser = argparse.ArgumentParser(
        description='Ledger - Personal Finance Manager',
    )
    parser.add_argument('--host', default=None, help='绑定地址')
    parser.add_argument('--port', type=int, default=None, help='端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    args = parser.parse_args()

    # ─── 单实例检查 ───
    if _try_signal_existing():
        sys.exit(0)
    _acquire_lock()

    # 合并参数
    port = args.port or _cfg('port')
    debug = args.debug

    if port == 0 or (_cfg('auto_port') and not args.port):
        port = _find_free_port()
    _port = port
    os.environ['WEB_PORT'] = str(port)

    host = args.host or _cfg('service_host') or '127.0.0.1'
    version = _get_version()

    # ─── 启动 Flask ───
    flask_thread = threading.Thread(
        target=run_flask, args=(host, port), daemon=True
    )
    flask_thread.start()
    _flask_ready.wait(timeout=10)

    # ─── 启动托盘 ───
    start_tray()

    # ─── 自动打开浏览器 ───
    if not args.no_browser:
        webbrowser.open(f'http://127.0.0.1:{port}')

    # ─── 全局快捷键 ───
    threading.Thread(target=_start_global_hotkey, daemon=True).start()

    # ─── 信号文件检查（第二次双击 exe → 浏览器打开）───
    def _signal_watcher():
        while True:
            if _check_signal_file():
                webbrowser.open(f'http://127.0.0.1:{port}')
            time.sleep(0.5)
    threading.Thread(target=_signal_watcher, daemon=True).start()

    # ─── 输出信息 ───
    _println("=" * 50)
    _println(f"  Ledger {version}")
    _println(f"  Address: http://127.0.0.1:{port}")
    _println(f"  Settings: http://127.0.0.1:{port}/settings")
    _println("=" * 50)

    update_tray_tooltip(f'Ledger {version}')

    # ─── 保持运行 ───
    def _shutdown(sig=None, frame=None):
        _println("\n[INFO] Shutting down...")
        if _tray:
            try:
                _tray.stop()
            except Exception:
                pass
        shutdown_flask()
        _release_lock()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # 阻塞主线程（Flask 在子线程中运行）
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()


if __name__ == '__main__':
    main()
