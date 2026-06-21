#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面应用配置管理 - JSON 配置文件读写
配置文件位置: exe 同目录的 ledger_desktop.json
"""

import os
import json
import copy
import sys

# ─── 路径 ──────────────────────────────────────────

if getattr(sys, 'frozen', False):
    _BUNDLE_DIR = os.path.dirname(sys.executable)
else:
    _BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(_BUNDLE_DIR, 'ledger_desktop.json')

# ─── 默认值 ────────────────────────────────────────

DEFAULTS = {
    # 服务
    "host": "127.0.0.1",
    "port": 5800,
    "auto_port": True,          # 自动找可用端口

    # 数据库
    "db_path": "",              # 空 = 默认 data/ledger.db

    # 系统
    "auto_start": False,        # 开机自启
    "language": "zh-CN",

    # 绑定地址
    "service_host": "127.0.0.1",  # 127.0.0.1 仅本机；0.0.0.0 允许外部访问
}

# ─── 读写 ──────────────────────────────────────────

_settings = {}


def load():
    """加载配置文件，不存在则创建默认配置"""
    global _settings
    _settings = copy.deepcopy(DEFAULTS)

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 合并：文件中的值覆盖默认值
            for key in DEFAULTS:
                if key in data:
                    _settings[key] = data[key]
        except (json.JSONDecodeError, IOError) as e:
            print(f"[WARN] 配置文件读取失败: {e}", file=sys.stderr)

    return _settings


def save():
    """保存当前配置到文件"""
    global _settings
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(_settings, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"[ERROR] 配置文件保存失败: {e}", file=sys.stderr)
        return False


def get(key=None):
    """获取配置，key=None 返回全部"""
    if not _settings:
        load()
    if key is None:
        return copy.deepcopy(_settings)
    return _settings.get(key, DEFAULTS.get(key))


def set(key, value):
    """设置单个配置项"""
    global _settings
    if not _settings:
        load()
    if key in DEFAULTS:
        # 类型校验
        expected = type(DEFAULTS[key])
        if expected == bool and isinstance(value, str):
            value = value.lower() in ('true', '1', 'yes')
        elif expected == int and isinstance(value, str):
            value = int(value)
        _settings[key] = value
        return True
    return False


def update(data: dict):
    """批量更新配置"""
    global _settings
    if not _settings:
        load()
    changed = []
    for key, value in data.items():
        if key in DEFAULTS:
            expected = type(DEFAULTS[key])
            if expected == bool and isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes')
            elif expected == int and isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                    continue
            _settings[key] = value
            changed.append(key)
    return changed


def reset():
    """恢复默认配置"""
    global _settings
    _settings = copy.deepcopy(DEFAULTS)
    save()


# ─── 开机自启管理 ────────────────────────────────────

def set_autostart_windows(enable: bool, exe_path: str = None):
    """Windows: 使用注册表 Run 键设置开机自启（无需管理员权限）"""
    if sys.platform != 'win32':
        return False, "仅支持 Windows"

    import winreg
    reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "Ledger"

    if not exe_path:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                # 值为 "exe路径" --no-browser
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}" --no-browser')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # 不存在也视为成功
        return True, "设置成功"
    except Exception as e:
        return False, str(e)


def set_autostart_linux(enable: bool, service_name: str = "ledger-web"):
    """Linux: 使用 systemd 设置开机自启"""
    if sys.platform == 'win32':
        return False, "不支持 Windows"

    import subprocess

    if enable:
        # 生成 service 文件
        exe_path = os.path.abspath(sys.argv[0])
        service_content = f"""[Unit]
Description=Ledger Web Service
After=network.target

[Service]
Type=simple
ExecStart={exe_path} --service
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
        service_path = f"/etc/systemd/system/{service_name}.service"
        try:
            with open(service_path, 'w') as f:
                f.write(service_content)
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', service_name], check=True)
            return True, "设置成功"
        except PermissionError:
            return False, "需要 root 权限 (sudo)"
    else:
        try:
            subprocess.run(['systemctl', 'disable', service_name], check=True)
            service_path = f"/etc/systemd/system/{service_name}.service"
            if os.path.exists(service_path):
                os.remove(service_path)
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            return True, "已取消开机自启"
        except Exception as e:
            return False, str(e)


def get_autostart_status():
    """检查当前自启状态"""
    if sys.platform == 'win32':
        import winreg
        reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, "Ledger")
                return True
        except FileNotFoundError:
            return False
    else:
        service_path = "/etc/systemd/system/ledger-web.service"
        return os.path.exists(service_path)
