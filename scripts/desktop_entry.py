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
_open_ui_callback = None
_open_settings_callback = None
_window_show_callback = None # 重建桌面窗口


def _create_tray_icon():
    """创建系统托盘图标（使用 run_detached，不阻塞调用线程）"""
    global _tray, _tray_ready

    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        _println("[WARN] pystray/Pillow 未安装，无系统托盘")
        _tray_ready.set()
        return

    # 生成一个简单的蓝色圆形图标
    def make_icon():
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # 蓝色圆形
        draw.ellipse([4, 4, 60, 60], fill=(9, 132, 227, 255))
        # 白色 L 字母
        draw.text((18, 14), "L", fill=(255, 255, 255, 255))
        return image

    def on_open_ui(icon, item):
        if _window_show_callback:
            _window_show_callback()
        elif _open_ui_callback:
            _open_ui_callback()

    def on_open_settings(icon, item):
        if _open_settings_callback:
            _open_settings_callback()

    def on_exit(icon, item):
        icon.stop()
        shutdown_flask()
        _release_lock()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem('打开界面', on_open_ui, default=True),
        pystray.MenuItem('设置', on_open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('退出', on_exit),
    )

    def _setup_visible(icon):
        """run_detached 的 setup 回调：标记图标可见"""
        icon.visible = True

    _tray = pystray.Icon(
        name='ledger',
        icon=make_icon(),
        title=f'Ledger {_get_version()}',
        menu=menu,
    )

    # 使用 run_detached：不阻塞调用线程，在内部线程中创建消息循环
    # pystray 文档要求 run() 在主线程，但 run_detached() 可在任意线程
    try:
        _tray.run_detached(setup=_setup_visible)
        _println("[INFO] 系统托盘已启动 (run_detached)")
    except Exception as e:
        _println(f"[ERROR] 托盘图标启动失败: {e}")
        _tray = None

    _tray_ready.set()

    # 延迟后尝试将托盘图标提升到任务栏可见区域
    def _delayed_promote():
        time.sleep(2)  # 等待 Windows 注册图标
        _promote_tray_icon()
    threading.Thread(target=_delayed_promote, daemon=True).start()

    # 延迟显示启动通知
    def _show_startup_notification():
        time.sleep(2)  # 等待托盘完全初始化
        try:
            if _tray:
                _tray.notify(
                    "Ledger 已启动",
                    "应用正在后台运行。\n右键此图标可打开界面或退出。\n快捷键 Ctrl+Shift+L 可恢复窗口。"
                )
        except Exception:
            pass

    threading.Thread(target=_show_startup_notification, daemon=True).start()


def start_tray():
    """在后台线程启动托盘"""
    t = threading.Thread(target=_create_tray_icon, daemon=True)
    t.start()
    _tray_ready.wait(timeout=5)


def _show_tray_notification(title, message):
    """显示 Windows 通知提醒用户托盘图标位置"""
    if _tray is None:
        return
    try:
        # pystray 的 notify 方法在 Windows 上显示气泡通知
        _tray.notify(title, message)
    except Exception:
        # 某些 pystray 版本或平台可能不支持 notify
        pass


def update_tray_tooltip(text):
    """更新托盘提示文字"""
    if _tray:
        try:
            _tray.title = text
        except Exception:
            pass


# ─── Windows 原生通知 + 全局快捷键 ──────────────────────

def _show_windows_messagebox(title, message):
    """使用 Windows 原生 MessageBox 显示通知（保证用户可见，不依赖托盘图标）"""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        MB_ICONINFORMATION = 0x40

        def _show():
            try:
                ctypes.windll.user32.MessageBoxW(0, message, title, MB_ICONINFORMATION)
            except Exception:
                pass
        threading.Thread(target=_show, daemon=True).start()
    except Exception:
        pass


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
            _println("[WARN] 全局快捷键 Ctrl+Shift+L 注册失败（可能被其他程序占用）")
            return

        _println("[INFO] 全局快捷键 Ctrl+Shift+L 已注册（轻量模式下可用）")

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:  # WM_HOTKEY
                _println("[INFO] 检测到快捷键 Ctrl+Shift+L，正在打开界面...")
                if _window_show_callback:
                    _window_show_callback()
                elif _open_ui_callback:
                    _open_ui_callback()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception as e:
        _println(f"[WARN] 全局快捷键线程异常: {e}")
    finally:
        try:
            import ctypes
            ctypes.windll.user32.UnregisterHotKey(None, 1)
        except Exception:
            pass


def _promote_tray_icon():
    """让 Windows 11 在任务栏显示托盘图标（不藏到溢出区）
    通过修改 HKCU\\Control Panel\\NotifyIconSettings 中的 IsPromoted 值实现"""
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
                                _println(f"[INFO] 托盘图标已设为任务栏可见")
                                return
                        except FileNotFoundError:
                            pass
                    i += 1
                except OSError:
                    break
        _println(f"[INFO] 托盘图标注册表条目未找到（首次运行，图标可能在溢出区）")
    except Exception as e:
        _println(f"[WARN] 托盘图标提升失败: {e}")


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
        if (confirm(
            '切换到轻量模式？\\n\\n' +
            '窗口将隐藏，服务继续在后台运行。\\n\\n' +
            '恢复方式（三选一）：\\n' +
            '  1. 右键系统托盘蓝色 L 图标 → 打开界面\\n' +
            '  2. 再次双击 exe 文件\\n' +
            '  3. 按 Ctrl+Shift+L 快捷键\\n\\n' +
            '如果找不到托盘图标，请点击任务栏右侧的 ∧ 箭头。\\n\\n' +
            '确认切换？'
        )) {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.switch_to_service();
            }
        }
    };
})();
""" % TOOLBAR_CSS


# ─── 桌面模式 ──────────────────────────────────────

def run_desktop_mode(port, width, height, debug):
    """桌面模式：pywebview 窗口 + Flask + 托盘（支持轻量模式窗口重建）"""
    try:
        import webview
    except ImportError:
        print("[ERROR] pywebview 未安装，请运行: pip install pywebview", file=sys.stderr)
        sys.exit(1)

    from web.app import app
    from scripts.webview_api import DesktopAPI

    global _open_ui_callback, _open_settings_callback
    global _window_show_callback

    _main_window = [None]
    _settings_window = [None]
    _switched_to_service = [False]
    _port = port
    _version = _get_version()

    # 启动 Flask
    flask_thread = threading.Thread(
        target=run_flask, args=('127.0.0.1', port), daemon=True
    )
    flask_thread.start()
    _flask_ready.wait(timeout=10)

    # 启动托盘（后台线程）
    start_tray()

    # ── 轻量模式核心：窗口重建信号 ──
    _relaunch_event = threading.Event()
    _exit_requested = [False]

    def inject_toolbar(win):
        try:
            win.evaluate_js(TOOLBAR_JS)
        except Exception:
            pass

    def open_settings():
        """打开设置（窗口存在用 pywebview，否则用浏览器）"""
        if _main_window[0] is not None:
            # 窗口在前台，用 pywebview 子窗口
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
            # 轻量模式（无窗口），用浏览器
            import webbrowser
            webbrowser.open(f'http://127.0.0.1:{_port}')

    def show_window():
        """托盘「打开界面」：触发主线程重建窗口"""
        _relaunch_event.set()

    def switch_to_service():
        """轻量模式：销毁窗口释放内存，Flask + 托盘继续"""
        _switched_to_service[0] = True
        if _main_window[0] is not None:
            try:
                _main_window[0].destroy()  # 释放浏览器引擎内存
            except Exception:
                pass
        update_tray_tooltip(f'Ledger {_version} (轻量模式)')
        # 显示 Windows 原生对话框（保证可见，不依赖托盘图标）
        _show_windows_messagebox(
            "Ledger - 已切换到轻量模式",
            "界面已隐藏，服务继续在后台运行。\n\n"
            "恢复界面的方式：\n"
            "  ● 右键系统托盘蓝色 \"L\" 图标 → 打开界面\n"
            "  ● 再次双击 exe 文件\n"
            "  ● 按 Ctrl+Shift+L 快捷键\n\n"
            "如果找不到托盘图标，请点击任务栏右侧的 ∧ 箭头，\n"
            "找到蓝色圆形 \"L\" 图标。"
        )
        # 同时尝试托盘气泡通知
        _show_tray_notification(
            "Ledger 已切换到轻量模式",
            "右键托盘图标或按 Ctrl+Shift+L 可恢复界面。"
        )

    def on_main_closed():
        """窗口关闭事件"""
        if not _switched_to_service[0]:
            # 用户手动点 X
            if _cfg('minimize_to_tray'):
                # 配置了最小化到托盘 → 转为轻量模式
                _println("[INFO] 窗口关闭，最小化到托盘...")
                _switched_to_service[0] = True
                # 这里不需要 destroy，窗口已经关闭了
                # webview.start() 会返回，主循环会处理后续
                # 更新托盘提示
                _show_windows_messagebox(
                    "Ledger - 已最小化到托盘",
                    "应用正在后台运行。\n\n"
                    "恢复界面的方式：\n"
                    "  ● 右键系统托盘蓝色 \"L\" 图标 → 打开界面\n"
                    "  ● 再次双击 exe 文件\n"
                    "  ● 按 Ctrl+Shift+L 快捷键\n\n"
                    "如果找不到托盘图标，请点击任务栏右侧的 ∧ 箭头。"
                )
                _show_tray_notification(
                    "Ledger 已最小化",
                    "右键托盘图标或按 Ctrl+Shift+L 可恢复界面。"
                )
            else:
                # 彻底退出
                _exit_requested[0] = True
                shutdown_flask()
                if _tray:
                    _tray.stop()
                _release_lock()
                os._exit(0)
        # 轻量模式：destroy() 触发 → webview.start() 返回 → 主循环处理

    def open_in_browser():
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{_port}')

    def quit_application():
        """退出整个应用：关闭窗口、停止 Flask、释放锁"""
        _println("[INFO] 用户请求退出...")
        _exit_requested[0] = True
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

    # 注册回调
    _open_ui_callback = open_in_browser
    _open_settings_callback = open_settings
    _window_show_callback = show_window

    # 创建 API
    api = DesktopAPI(on_switch_to_service=switch_to_service, on_quit=quit_application)
    api.open_settings = open_settings

    _println("=" * 50)
    _println(f"  Ledger Desktop {_version}")
    _println("=" * 50)
    _println(f"  Database:  {os.environ.get('LEDGER_DB_PATH', '?')}")
    _println(f"  Address:   http://127.0.0.1:{port}")
    _println("  托盘:      右键图标可操作")
    _println("  快捷键:    Ctrl+Shift+L 恢复窗口")
    _println("  工具栏:    顶部「设置」和「轻量模式」按钮")
    _println("=" * 50)

    # 启动信号文件检查线程（检测第二次双击 exe）
    def _signal_watcher():
        while not _exit_requested[0]:
            if _check_signal_file():
                _println("[INFO] 收到唤醒信号，正在打开界面...")
                _relaunch_event.set()
            time.sleep(0.5)
    watcher = threading.Thread(target=_signal_watcher, daemon=True)
    watcher.start()

    # 启动全局快捷键监听 (Ctrl+Shift+L)
    hotkey_thread = threading.Thread(
        target=_start_global_hotkey, args=(_relaunch_event,), daemon=True
    )
    hotkey_thread.start()

    # ══════════════════════════════════════════════════
    #  主循环：窗口创建 → 运行 → 销毁 → 等待信号 → 重建
    # ══════════════════════════════════════════════════
    while not _exit_requested[0]:
        _switched_to_service[0] = False
        _relaunch_event.clear()

        # 创建主窗口
        _main_window[0] = webview.create_window(
            title=f'Ledger 记账系统 {_version}',
            url=f'http://127.0.0.1:{port}',
            width=width, height=height,
            min_size=(900, 600),
            text_select=True, js_api=api,
        )
        _main_window[0].events.closed += on_main_closed
        _main_window[0].events.loaded += lambda: inject_toolbar(_main_window[0])

        update_tray_tooltip(f'Ledger {_version}')

        # 启动 pywebview（阻塞，窗口关闭后返回）
        webview.start(debug=debug)

        if _exit_requested[0]:
            break

        # ── 窗口已销毁（轻量模式），内存已释放 ──
        _main_window[0] = None
        _settings_window[0] = None
        _println(f"[INFO] 轻量模式：界面已关闭，服务继续运行")
        update_tray_tooltip(f'Ledger {_version} (轻量模式)')

        # 等待「打开界面」信号 → 重建窗口
        while not _relaunch_event.is_set():
            if _exit_requested[0]:
                break
            _relaunch_event.wait(timeout=1.0)

        if not _exit_requested[0]:
            _println("[INFO] 正在恢复桌面窗口...")

    _release_lock()


# ─── 服务模式 ──────────────────────────────────────

def run_service_mode(host, port, debug):
    """纯服务模式：Flask + 托盘，无窗口"""
    from web.app import app

    global _open_ui_callback, _open_settings_callback

    # 启动托盘
    start_tray()

    def open_in_browser():
        """服务模式下用浏览器打开界面"""
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{port}')

    _open_ui_callback = open_in_browser
    _open_settings_callback = open_in_browser

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
                _println("[INFO] 收到唤醒信号，正在打开浏览器...")
                if _open_ui_callback:
                    _open_ui_callback()
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
