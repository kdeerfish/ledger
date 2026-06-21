#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger 统一入口 - 桌面应用 + 系统托盘 + 服务模式

启动流程:
  1. 双击 exe → 读取 launch_with_gui 配置
     - True  → 桌面窗口 + Flask + 托盘（可随时切换到服务模式）
     - False → 纯服务 + 托盘（无窗口）
  2. --service → 强制纯服务模式
  3. --settings → 仅打开设置窗口
"""

import os
import sys
import time
import signal
import threading
import argparse

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
        # 实例在运行，写入信号文件通知它打开界面
        try:
            with open(SIGNAL_FILE, 'w') as f:
                f.write(str(os.getpid()))
            _println(f"[INFO] Ledger 已在运行 (PID {old_pid})，正在打开界面...")
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
# 桌面模式下由 run_desktop_mode 注册的回调
_tray_on_open_ui = None
_tray_on_open_settings = None
_tray_on_toggle_mode = None   # 切换服务/桌面模式


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
        if _tray_on_open_ui:
            _tray_on_open_ui()

    def on_open_settings(icon, item):
        if _tray_on_open_settings:
            _tray_on_open_settings()

    def on_toggle_mode(icon, item):
        if _tray_on_toggle_mode:
            _tray_on_toggle_mode()

    def on_exit(icon, item):
        icon.stop()
        shutdown_flask()
        _release_lock()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem('打开界面', on_open_ui, default=True),
        pystray.MenuItem('设置', on_open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('切换为仅服务模式', on_toggle_mode),
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

def _start_global_hotkey(relaunch_event):
    """注册全局快捷键 Ctrl+Shift+L 恢复窗口（仅 Windows）"""
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
                if _tray_on_open_ui:
                    _tray_on_open_ui()
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


# ─── 主窗口注入的工具栏 HTML ──────────────────────────

TOOLBAR_CSS = """
#ledger-toolbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 36px;
    background: #2d3436;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 0 12px;
    z-index: 99999;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    -webkit-app-region: drag;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}
#ledger-toolbar .tb-btn {
    -webkit-app-region: no-drag;
    padding: 4px 12px;
    margin-left: 6px;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    color: #dfe6e9;
    background: rgba(255,255,255,0.1);
    transition: background 0.2s;
}
#ledger-toolbar .tb-btn:hover { background: rgba(255,255,255,0.2); }
#ledger-toolbar .tb-btn.danger { color: #ff7675; }
#ledger-toolbar .tb-btn.danger:hover { background: rgba(255,118,117,0.2); }
#ledger-toolbar .tb-label {
    -webkit-app-region: no-drag;
    color: #b2bec3;
    font-size: 11px;
    margin-right: auto;
}
body { padding-top: 36px !important; }
"""

TOOLBAR_JS = """
(function() {
    if (document.getElementById('ledger-toolbar')) return;
    var css = document.createElement('style');
    css.textContent = `%s`;
    document.head.appendChild(css);

    var bar = document.createElement('div');
    bar.id = 'ledger-toolbar';
    bar.innerHTML = `
        <span class="tb-label">Ledger</span>
        <button class="tb-btn" onclick="openSettings()">⚙ 设置</button>
        <button class="tb-btn danger" onclick="switchToService()">⏻ 轻量模式</button>
    `;
    document.body.prepend(bar);

    window.openSettings = function() {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.open_settings();
        }
    };
    window.switchToService = function() {
        if (confirm('切换到轻量模式？\\n窗口将隐藏，服务继续在后台运行。\\n\\n可从托盘图标恢复界面。')) {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.switch_to_service();
            }
        }
    };
})();
""" % TOOLBAR_CSS


# ─── 桌面模式 ──────────────────────────────────────

# 关闭对话框 HTML
CLOSE_DIALOG_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>关闭</title>
<style>
body{margin:0;font-family:"Microsoft YaHei",sans-serif;background:#f5f6fa;display:flex;
flex-direction:column;align-items:center;justify-content:center;height:100vh}
.box{background:#fff;border-radius:12px;padding:32px;box-shadow:0 2px 12px rgba(0,0,0,.1);text-align:center;max-width:380px}
h3{margin:0 0 8px;color:#2d3436}p{color:#636e72;margin:0 0 20px;font-size:14px}
.btns{display:flex;gap:12px;justify-content:center}
.btn{padding:10px 24px;border:none;border-radius:8px;font-size:14px;cursor:pointer}
.btn-min{background:#0984e3;color:#fff}.btn-min:hover{background:#0769b5}
.btn-exit{background:#dfe6e9;color:#2d3436}.btn-exit:hover{background:#b2bec3}
.remember{margin-top:16px;font-size:12px;color:#b2bec3}
.remember label{cursor:pointer}
</style></head><body>
<div class="box">
<h3>关闭 Ledger</h3>
<p>你想怎么处理？</p>
<div class="btns">
<button class="btn btn-min" onclick="choose('minimize')">缩小到托盘</button>
<button class="btn btn-exit" onclick="choose('exit')">关闭整个系统</button>
</div>
<div class="remember"><label><input type="checkbox" id="remember"> 以后都这么选择</label></div>
</div>
<script>
function choose(action){
  var remember=document.getElementById('remember').checked;
  if(window.pywebview&&window.pywebview.api){
    window.pywebview.api.close_dialog_result(action,remember);
  }
}
</script></body></html>"""

# 加载中遮罩 HTML（轻量模式恢复时显示）
LOADING_OVERLAY_JS = """
(function(){
  if(document.getElementById('ledger-loading'))return;
  var d=document.createElement('div');
  d.id='ledger-loading';
  d.style.cssText='position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(245,246,250,.95);z-index:999999;display:flex;align-items:center;justify-content:center;font-family:Microsoft YaHei,sans-serif';
  d.innerHTML='<div style="text-align:center"><div style="font-size:32px;margin-bottom:16px">⏳</div><div style="color:#636e72;font-size:14px">正在加载界面...</div></div>';
  document.body.appendChild(d);
  setTimeout(function(){var o=document.getElementById('ledger-loading');if(o)o.remove()},8000);
})();
"""


def run_desktop_mode(port, width, height, debug):
    """桌面模式：pywebview 窗口 + Flask + 托盘（轻量模式释放窗口内存）"""
    try:
        import webview
    except ImportError:
        print("[ERROR] pywebview 未安装，请运行: pip install pywebview", file=sys.stderr)
        sys.exit(1)

    from scripts.webview_api import DesktopAPI

    global _tray_on_open_ui, _tray_on_open_settings, _tray_on_toggle_mode

    _main_window = [None]
    _settings_window = [None]
    _is_lightweight = [False]
    _relaunch = threading.Event()
    _quit = [False]
    _version = _get_version()
    _close_dialog_window = [None]

    # 启动 Flask
    flask_thread = threading.Thread(
        target=run_flask, args=('127.0.0.1', port), daemon=True
    )
    flask_thread.start()
    _flask_ready.wait(timeout=10)

    # 启动托盘
    start_tray()

    # ── 回调 ──────────────────────────────────────

    def inject_toolbar(win):
        try:
            win.evaluate_js(TOOLBAR_JS)
        except Exception:
            pass

    def show_loading(win):
        """在窗口中注入加载遮罩"""
        try:
            win.evaluate_js(LOADING_OVERLAY_JS)
        except Exception:
            pass

    def do_open_ui():
        if _main_window[0] is not None:
            try:
                _main_window[0].evaluate_js(
                    'window.focus(); document.title=document.title;'
                )
            except Exception:
                pass
        else:
            _relaunch.set()

    def do_open_settings():
        if _main_window[0] is not None:
            if _settings_window[0] is not None:
                try:
                    _settings_window[0].show()
                    return
                except Exception:
                    pass
            settings_path = os.path.join(MEIPASS_DIR, 'frontend', 'settings.html')
            _settings_window[0] = webview.create_window(
                'Ledger 设置',
                url=f'file:///{settings_path}',
                width=680, height=520,
                resizable=True, js_api=api,
            )
        else:
            _relaunch.set()

    def do_switch_to_service():
        _is_lightweight[0] = True
        _relaunch.clear()
        if _main_window[0] is not None:
            try:
                _main_window[0].destroy()
            except Exception:
                pass
        update_tray_tooltip(f'Ledger {_version} (轻量模式)')

    def do_toggle_mode():
        """托盘切换服务/桌面模式"""
        current = _cfg('service_mode')
        desktop_config.set('service_mode', not current)
        desktop_config.save()
        if not current:
            # 切到服务模式：销毁窗口
            do_switch_to_service()
        else:
            # 切到桌面模式：重建窗口
            _relaunch.set()

    def do_quit():
        _quit[0] = True
        if _main_window[0] is not None:
            try:
                _main_window[0].destroy()
            except Exception:
                pass
        shutdown_flask()
        if _tray:
            try:
                _tray.stop()
            except Exception:
                pass
        _release_lock()
        os._exit(0)

    def show_close_dialog():
        """显示关闭选择对话框"""
        if _close_dialog_window[0] is not None:
            try:
                _close_dialog_window[0].show()
                return
            except Exception:
                pass
        dialog = webview.create_window(
            '关闭 Ledger',
            html=CLOSE_DIALOG_HTML,
            width=420, height=260,
            resizable=False, frameless=True,
            js_api=api,
        )
        _close_dialog_window[0] = dialog

    def on_close_dialog_result(action, remember):
        """关闭对话框的回调"""
        if _close_dialog_window[0] is not None:
            try:
                _close_dialog_window[0].destroy()
            except Exception:
                pass
            _close_dialog_window[0] = None
        if remember:
            desktop_config.set('close_action', action)
            desktop_config.save()
        if action == 'minimize':
            do_switch_to_service()
        else:
            do_quit()

    def on_window_closed():
        """pywebview 窗口关闭事件"""
        if _is_lightweight[0]:
            return  # 轻量模式触发的关闭，忽略
        action = _cfg('close_action')
        if action == 'minimize':
            do_switch_to_service()
        elif action == 'exit':
            do_quit()
        else:
            # ask: 弹出选择对话框
            show_close_dialog()

    # 注册回调
    _tray_on_open_ui = do_open_ui
    _tray_on_open_settings = do_open_settings
    _tray_on_toggle_mode = do_toggle_mode

    def on_mode_switch(is_service):
        """设置页切换模式"""
        if is_service:
            do_switch_to_service()
        else:
            _relaunch.set()

    api = DesktopAPI(
        on_switch_to_service=do_switch_to_service,
        on_quit=do_quit,
        on_close_dialog_result=on_close_dialog_result,
        on_mode_switch=on_mode_switch,
    )
    api.open_settings = do_open_settings

    # 启动快捷键
    threading.Thread(
        target=_start_global_hotkey, args=(_relaunch,), daemon=True
    ).start()

    # 启动信号文件检查
    def _signal_watcher():
        while not _quit[0]:
            if _check_signal_file():
                do_open_ui()
            time.sleep(0.5)
    threading.Thread(target=_signal_watcher, daemon=True).start()

    _println("=" * 50)
    _println(f"  Ledger Desktop {_version}")
    _println(f"  Address: http://127.0.0.1:{port}")
    _println("=" * 50)

    # ════════════════════════════════════════════════
    #  主循环：创建窗口 → 运行 → (轻量模式) → 等待 → 重建
    # ════════════════════════════════════════════════
    while not _quit[0]:
        _is_lightweight[0] = False
        _relaunch.clear()

        _main_window[0] = webview.create_window(
            title=f'Ledger 记账系统 {_version}',
            url=f'http://127.0.0.1:{port}',
            width=width, height=height,
            min_size=(900, 600),
            text_select=True, js_api=api,
        )
        _main_window[0].events.closed += on_window_closed
        _main_window[0].events.loaded += lambda: inject_toolbar(_main_window[0])

        update_tray_tooltip(f'Ledger {_version}')
        webview.start(debug=debug)

        if _quit[0]:
            break

        # 窗口已销毁（轻量模式）
        _main_window[0] = None
        _settings_window[0] = None
        update_tray_tooltip(f'Ledger {_version} (轻量模式)')

        # 等待「打开界面」信号
        while not _relaunch.is_set():
            if _quit[0]:
                break
            _relaunch.wait(timeout=1.0)

    _release_lock()


# ─── 服务模式 ──────────────────────────────────────

def run_service_mode(host, port, debug):
    """纯服务模式：Flask + 托盘，无窗口"""
    from web.app import app

    global _tray_on_open_ui, _tray_on_open_settings

    start_tray()

    def open_in_browser():
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{port}')

    def open_settings_in_browser():
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{port}/settings')

    _tray_on_open_ui = open_in_browser
    _tray_on_open_settings = open_settings_in_browser

    _println("=" * 50)
    _println("  Ledger - Service Mode")
    _println("=" * 50)
    _println(f"  Database: {os.environ.get('LEDGER_DB_PATH', '?')}")
    _println(f"  Address:  http://{host}:{port}")
    _println(f"  托盘:     右键图标可操作")
    _println("  Press Ctrl+C to stop")
    _println("=" * 50)

    # 启动信号文件检查线程，用于检测第二次双击 exe 时唤醒已有实例
    def _signal_watcher():
        while True:
            if _check_signal_file():
                if _tray_on_open_ui:
                    _tray_on_open_ui()
            time.sleep(0.5)
    watcher = threading.Thread(target=_signal_watcher, daemon=True)
    watcher.start()

    def _shutdown(sig, frame):
        _println("\n[INFO] Shutting down...")
        if _tray:
            _tray.stop()
        shutdown_flask()
        _release_lock()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    app.run(host=host, port=port, debug=debug, use_reloader=False)


# ─── 主入口 ────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Ledger - Personal Finance Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
模式说明:
  默认              读取配置决定是否显示界面
  --gui             强制显示桌面窗口
  --service         强制纯服务模式（无窗口）
  --settings        仅打开设置窗口
        """,
    )
    parser.add_argument('--gui', action='store_true',
                        help='强制显示桌面窗口')
    parser.add_argument('--service', action='store_true',
                        help='服务模式：仅运行 Flask，不显示窗口')
    parser.add_argument('--settings', action='store_true',
                        help='仅打开设置窗口')
    parser.add_argument('--host', default=None,
                        help='绑定地址')
    parser.add_argument('--port', type=int, default=None,
                        help='端口')
    parser.add_argument('--width', type=int, default=None,
                        help='窗口宽度')
    parser.add_argument('--height', type=int, default=None,
                        help='窗口高度')
    parser.add_argument('--debug', action='store_true',
                        help='调试模式')
    args = parser.parse_args()

    # ─── 单实例检查 ───
    if not args.settings:
        if _try_signal_existing():
            sys.exit(0)
        _acquire_lock()

    # 合并参数
    port = args.port or _cfg('port')
    width = args.width or _cfg('window_width')
    height = args.height or _cfg('window_height')
    debug = args.debug

    if port == 0 or (_cfg('auto_port') and not args.port):
        port = _find_free_port()
    os.environ['WEB_PORT'] = str(port)

    # ─── 仅设置窗口 ───
    if args.settings:
        try:
            import webview
        except ImportError:
            print("[ERROR] pywebview 未安装", file=sys.stderr)
            sys.exit(1)
        from scripts.webview_api import DesktopAPI
        api = DesktopAPI()
        settings_path = os.path.join(MEIPASS_DIR, 'frontend', 'settings.html')
        webview.create_window(
            'Ledger 设置',
            url=f'file:///{settings_path}',
            width=680,
            height=520,
            resizable=True,
            js_api=api,
        )
        webview.start()
        return

    # ─── 强制服务模式 ───
    if args.service:
        host = args.host or '0.0.0.0'
        run_service_mode(host, port, debug)
        return

    # ─── 读取配置决定模式 ───
    launch_with_gui = _cfg('launch_with_gui')

    # 强制桌面模式
    if args.gui:
        launch_with_gui = True

    if launch_with_gui:
        run_desktop_mode(port, width, height, debug)
    else:
        host = args.host or _cfg('service_host') or '0.0.0.0'
        run_service_mode(host, port, debug)


if __name__ == '__main__':
    main()
