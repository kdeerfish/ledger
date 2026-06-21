#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""desktop_config 模块测试"""

import os
import sys
import json
import tempfile
import pytest

# 确保能导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ledger_modules import desktop_config


@pytest.fixture(autouse=True)
def fresh_config(tmp_path, monkeypatch):
    """每个测试用临时配置文件"""
    cfg_file = tmp_path / 'ledger_desktop.json'
    monkeypatch.setattr(desktop_config, 'CONFIG_FILE', str(cfg_file))
    monkeypatch.setattr(desktop_config, '_settings', {})
    yield cfg_file


class TestLoad:
    def test_load_creates_defaults(self):
        cfg = desktop_config.load()
        assert cfg['host'] == '127.0.0.1'
        assert cfg['port'] == 5800
        assert cfg['auto_port'] is True
        assert cfg['auto_start'] is False
        assert cfg['service_host'] == '127.0.0.1'

    def test_load_from_file(self, fresh_config):
        fresh_config.write_text(json.dumps({
            'port': 9999,
            'auto_start': True,
        }), encoding='utf-8')
        cfg = desktop_config.load()
        assert cfg['port'] == 9999
        assert cfg['auto_start'] is True
        # 未设置的保持默认
        assert cfg['auto_port'] is True

    def test_load_invalid_json(self, fresh_config):
        fresh_config.write_text('not json {{{', encoding='utf-8')
        cfg = desktop_config.load()
        # 回退到默认值
        assert cfg['port'] == 5800

    def test_load_missing_file(self, fresh_config):
        # 文件不存在时用默认值
        cfg = desktop_config.load()
        assert cfg['port'] == 5800


class TestSave:
    def test_save_creates_file(self, fresh_config):
        desktop_config.load()
        desktop_config.set('port', 7777)
        result = desktop_config.save()
        assert result is True
        assert fresh_config.exists()

    def test_save_content(self, fresh_config):
        desktop_config.load()
        desktop_config.set('port', 7777)
        desktop_config.save()
        data = json.loads(fresh_config.read_text(encoding='utf-8'))
        assert data['port'] == 7777

    def test_save_readonly_dir(self, fresh_config):
        desktop_config.load()
        desktop_config.set('port', 7777)
        # 模拟写入失败
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(desktop_config, 'CONFIG_FILE', '/nonexistent/dir/file.json')
        result = desktop_config.save()
        assert result is False
        monkeypatch.undo()


class TestGet:
    def test_get_all(self):
        cfg = desktop_config.get()
        assert isinstance(cfg, dict)
        assert 'port' in cfg

    def test_get_single(self):
        desktop_config.load()
        assert desktop_config.get('port') == 5800

    def test_get_unknown_key(self):
        desktop_config.load()
        # 未知 key 返回默认值
        assert desktop_config.get('nonexistent') is None

    def test_get_returns_copy(self):
        desktop_config.load()
        cfg1 = desktop_config.get()
        cfg2 = desktop_config.get()
        cfg1['port'] = 9999
        assert cfg2['port'] == 5800  # 不受影响


class TestSet:
    def test_set_string_to_int(self):
        desktop_config.load()
        desktop_config.set('port', '8080')
        assert desktop_config.get('port') == 8080

    def test_set_string_to_bool(self):
        desktop_config.load()
        desktop_config.set('auto_start', 'true')
        assert desktop_config.get('auto_start') is True

    def test_set_bool_false(self):
        desktop_config.load()
        desktop_config.set('auto_start', 'false')
        assert desktop_config.get('auto_start') is False

    def test_set_unknown_key(self):
        desktop_config.load()
        result = desktop_config.set('nonexistent_key', 'value')
        assert result is False

    def test_set_before_load(self):
        # 未 load 时 set 也能工作
        result = desktop_config.set('port', 9999)
        assert result is True
        assert desktop_config.get('port') == 9999


class TestUpdate:
    def test_batch_update(self):
        desktop_config.load()
        desktop_config.update({'port': 3000, 'auto_start': True})
        assert desktop_config.get('port') == 3000
        assert desktop_config.get('auto_start') is True

    def test_update_before_load(self):
        """_settings 为空时 update 自动触发 load"""
        desktop_config._settings = {}
        changed = desktop_config.update({'port': 4000})
        assert 'port' in changed
        assert desktop_config.get('port') == 4000

    def test_update_ignores_unknown(self):
        desktop_config.load()
        desktop_config.update({'port': 3000, 'unknown_key': 'value'})
        assert desktop_config.get('port') == 3000

    def test_update_bool_from_string(self):
        desktop_config.load()
        desktop_config.update({'auto_port': 'false'})
        assert desktop_config.get('auto_port') is False

    def test_update_int_from_string(self):
        desktop_config.load()
        desktop_config.update({'port': '3000'})
        assert desktop_config.get('port') == 3000

    def test_update_invalid_int(self):
        desktop_config.load()
        desktop_config.update({'port': 'not_a_number'})
        assert desktop_config.get('port') == 5800


class TestReset:
    def test_reset_restores_defaults(self):
        desktop_config.load()
        desktop_config.set('port', 9999)
        desktop_config.set('auto_start', True)
        desktop_config.reset()
        cfg = desktop_config.get()
        assert cfg['port'] == 5800
        assert cfg['auto_start'] is False

    def test_reset_saves_to_file(self, fresh_config):
        desktop_config.load()
        desktop_config.set('port', 9999)
        desktop_config.save()
        desktop_config.reset()
        # 文件也被重置
        data = json.loads(fresh_config.read_text(encoding='utf-8'))
        assert data['port'] == 5800


class TestAutostartWindows:
    def test_autostart_windows_not_win32(self, monkeypatch):
        monkeypatch.setattr(sys, 'platform', 'linux')
        ok, msg = desktop_config.set_autostart_windows(True)
        assert ok is False
        assert '仅支持 Windows' in msg

    def test_autostart_enable(self, monkeypatch):
        """启用开机自启：写入注册表成功"""
        monkeypatch.setattr(sys, 'platform', 'win32')
        import winreg
        written = {}
        class MockKey:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def __setitem__(self, k, v): written[k] = v
        def mock_open_key(root, path, reserved, access):
            return MockKey()
        def mock_set_value_ex(key, name, reserved, type, value):
            written[name] = value
        def mock_delete_value(key, name):
            written.pop(name, None)
        monkeypatch.setattr(winreg, 'OpenKey', mock_open_key)
        monkeypatch.setattr(winreg, 'SetValueEx', mock_set_value_ex)
        monkeypatch.setattr(winreg, 'DeleteValue', mock_delete_value)
        ok, msg = desktop_config.set_autostart_windows(True, exe_path='C:\\test.exe')
        assert ok is True
        assert 'Ledger' in written

    def test_autostart_disable(self, monkeypatch):
        """禁用开机自启：删除注册表键"""
        monkeypatch.setattr(sys, 'platform', 'win32')
        import winreg
        deleted = []
        class MockKey:
            def __enter__(self): return self
            def __exit__(self, *a): pass
        def mock_open_key(root, path, reserved, access):
            return MockKey()
        def mock_delete_value(key, name):
            deleted.append(name)
        monkeypatch.setattr(winreg, 'OpenKey', mock_open_key)
        monkeypatch.setattr(winreg, 'DeleteValue', mock_delete_value)
        ok, msg = desktop_config.set_autostart_windows(False)
        assert ok is True
        assert 'Ledger' in deleted

    def test_autostart_disable_not_exists(self, monkeypatch):
        """禁用时键不存在也应成功"""
        monkeypatch.setattr(sys, 'platform', 'win32')
        import winreg
        class MockKey:
            def __enter__(self): return self
            def __exit__(self, *a): pass
        def mock_open_key(root, path, reserved, access):
            return MockKey()
        def mock_delete_value(key, name):
            raise FileNotFoundError()
        monkeypatch.setattr(winreg, 'OpenKey', mock_open_key)
        monkeypatch.setattr(winreg, 'DeleteValue', mock_delete_value)
        ok, msg = desktop_config.set_autostart_windows(False)
        assert ok is True

    def test_autostart_enable_error(self, monkeypatch):
        """注册表写入失败"""
        monkeypatch.setattr(sys, 'platform', 'win32')
        import winreg
        def mock_open_key(root, path, reserved, access):
            raise OSError('access denied')
        monkeypatch.setattr(winreg, 'OpenKey', mock_open_key)
        ok, msg = desktop_config.set_autostart_windows(True, exe_path='C:\\test.exe')
        assert ok is False
        assert 'access denied' in msg

    def test_autostart_default_exe_path(self, monkeypatch):
        """不传 exe_path 时使用默认路径"""
        monkeypatch.setattr(sys, 'platform', 'win32')
        import winreg
        written = {}
        class MockKey:
            def __enter__(self): return self
            def __exit__(self, *a): pass
        def mock_open_key(root, path, reserved, access):
            return MockKey()
        def mock_set_value_ex(key, name, reserved, type, value):
            written[name] = value
        monkeypatch.setattr(winreg, 'OpenKey', mock_open_key)
        monkeypatch.setattr(winreg, 'SetValueEx', mock_set_value_ex)
        ok, msg = desktop_config.set_autostart_windows(True)
        assert ok is True
        assert 'Ledger' in written
        # 值包含 --no-browser
        assert '--no-browser' in written['Ledger']

    def test_autostart_default_exe_frozen(self, monkeypatch):
        """frozen 模式下使用 sys.executable"""
        monkeypatch.setattr(sys, 'platform', 'win32')
        monkeypatch.setattr(sys, 'frozen', True, raising=False)
        monkeypatch.setattr(sys, 'executable', 'C:\\Ledger\\ledger.exe')
        import winreg
        written = {}
        class MockKey:
            def __enter__(self): return self
            def __exit__(self, *a): pass
        def mock_open_key(root, path, reserved, access):
            return MockKey()
        def mock_set_value_ex(key, name, reserved, type, value):
            written[name] = value
        monkeypatch.setattr(winreg, 'OpenKey', mock_open_key)
        monkeypatch.setattr(winreg, 'SetValueEx', mock_set_value_ex)
        ok, msg = desktop_config.set_autostart_windows(True)
        assert ok is True
        assert 'Ledger' in written
        assert 'ledger.exe' in written['Ledger'].lower()


class TestAutostartLinux:
    def test_not_win32(self, monkeypatch):
        monkeypatch.setattr(sys, 'platform', 'win32')
        ok, msg = desktop_config.set_autostart_linux(True)
        assert ok is False
        assert '不支持 Windows' in msg

    def test_enable(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, 'platform', 'linux')
        import subprocess
        def mock_run(cmd, **kwargs):
            return None
        monkeypatch.setattr(subprocess, 'run', mock_run)
        # mock open to avoid writing to /etc
        import builtins
        original_open = builtins.open
        def mock_open(path, *args, **kwargs):
            if '/etc/systemd' in str(path):
                from io import StringIO
                return StringIO()
            return original_open(path, *args, **kwargs)
        monkeypatch.setattr(builtins, 'open', mock_open)
        ok, msg = desktop_config.set_autostart_linux(True)
        assert ok is True

    def test_enable_permission_error(self, monkeypatch):
        monkeypatch.setattr(sys, 'platform', 'linux')
        import builtins
        def mock_open(path, *args, **kwargs):
            if '/etc/systemd' in str(path):
                raise PermissionError('denied')
            return builtins.open(path, *args, **kwargs)
        monkeypatch.setattr(builtins, 'open', mock_open)
        ok, msg = desktop_config.set_autostart_linux(True)
        assert ok is False
        assert 'root' in msg

    def test_disable(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, 'platform', 'linux')
        import subprocess
        def mock_run(cmd, **kwargs):
            return None
        monkeypatch.setattr(subprocess, 'run', mock_run)
        # mock os.path.exists and os.remove
        monkeypatch.setattr(os.path, 'exists', lambda p: True)
        monkeypatch.setattr(os, 'remove', lambda p: None)
        ok, msg = desktop_config.set_autostart_linux(False)
        assert ok is True

    def test_disable_exception(self, monkeypatch):
        monkeypatch.setattr(sys, 'platform', 'linux')
        import subprocess
        def mock_run(cmd, **kwargs):
            raise OSError('systemctl not found')
        monkeypatch.setattr(subprocess, 'run', mock_run)
        ok, msg = desktop_config.set_autostart_linux(False)
        assert ok is False
        assert 'systemctl not found' in msg


class TestAutostartStatus:
    def test_status_on_linux(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, 'platform', 'linux')
        monkeypatch.setattr(desktop_config, '_BUNDLE_DIR', str(tmp_path))
        assert desktop_config.get_autostart_status() is False

    def test_status_on_linux_exists(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, 'platform', 'linux')
        monkeypatch.setattr(desktop_config, '_BUNDLE_DIR', str(tmp_path))
        monkeypatch.setattr(os.path, 'exists', lambda p: 'ledger-web.service' in p)
        assert desktop_config.get_autostart_status() is True

    def test_status_on_windows(self, monkeypatch):
        """注册表中有 Ledger 键 → 已启用"""
        monkeypatch.setattr(sys, 'platform', 'win32')
        import winreg
        class MockKey:
            def __enter__(self): return self
            def __exit__(self, *a): pass
        def mock_open_key(root, path, reserved, access):
            return MockKey()
        def mock_query_value_ex(key, name):
            if name == 'Ledger':
                return ('"C:\\test.exe" --no-browser', winreg.REG_SZ)
            raise FileNotFoundError()
        monkeypatch.setattr(winreg, 'OpenKey', mock_open_key)
        monkeypatch.setattr(winreg, 'QueryValueEx', mock_query_value_ex)
        assert desktop_config.get_autostart_status() is True

    def test_status_on_windows_not_found(self, monkeypatch):
        """注册表中无 Ledger 键 → 未启用"""
        monkeypatch.setattr(sys, 'platform', 'win32')
        import winreg
        def mock_open_key(root, path, reserved, access):
            raise FileNotFoundError()
        monkeypatch.setattr(winreg, 'OpenKey', mock_open_key)
        assert desktop_config.get_autostart_status() is False
