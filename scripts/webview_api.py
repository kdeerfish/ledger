#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pywebview JavaScript Bridge API
提供 settings 窗口和主窗口调用的 Python 方法
"""

import os
import sys

# 路径兼容
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = os.path.dirname(sys.executable)
    MEIPASS_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEIPASS_DIR = BUNDLE_DIR


class DesktopAPI:
    """pywebview 暴露给 JS 的 API"""

    def __init__(self, on_switch_to_service=None, on_quit=None):
        from ledger_modules import desktop_config
        self._config = desktop_config
        self._on_switch_to_service = on_switch_to_service
        self._on_quit = on_quit

    def get_config(self):
        """获取全部配置"""
        cfg = self._config.get()
        # 附加只读信息
        cfg['_config_file'] = self._config.CONFIG_FILE
        cfg['_version'] = self._get_version()
        cfg['_db_path'] = os.environ.get('LEDGER_DB_PATH', '')
        cfg['_autostart'] = self._config.get_autostart_status()
        return cfg

    def save_config(self, data: dict):
        """保存配置"""
        try:
            self._config.update(data)
            self._config.save()

            # 应用需要立即生效的设置
            if 'port' in data:
                os.environ['WEB_PORT'] = str(data['port'])

            restart_required = 'service_mode' in data or 'host' in data
            return {'success': True, 'restart_required': restart_required}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def set_autostart(self, enable: bool):
        """设置开机自启"""
        try:
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = os.path.abspath(sys.argv[0])

            ok, msg = self._config.set_autostart_windows(enable, exe_path)
            if ok:
                self._config.set('auto_start', enable)
                self._config.save()
            return {'success': ok, 'error': msg}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def reset_config(self):
        """恢复默认"""
        try:
            self._config.reset()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def switch_to_service(self):
        """切换到轻量模式（销毁窗口，保留 Flask + 托盘）"""
        if self._on_switch_to_service:
            self._on_switch_to_service()
            return {'success': True}
        return {'success': False, 'error': 'callback not set'}

    def quit_app(self):
        """退出整个应用"""
        if self._on_quit:
            self._on_quit()
            return {'success': True}
        return {'success': False, 'error': 'callback not set'}

    def get_version(self):
        """获取版本号"""
        return self._get_version()

    def _get_version(self):
        try:
            import tomllib
            pyproject = os.path.join(MEIPASS_DIR, 'pyproject.toml')
            with open(pyproject, 'rb') as f:
                return 'v' + tomllib.load(f).get('project', {}).get('version', '0.0.0')
        except Exception:
            return 'v0.0.0'
