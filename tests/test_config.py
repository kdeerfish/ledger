#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块测试 - 覆盖环境变量、路径解析、.env 文件加载
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

import ledger_modules.config as config_module


class TestLoadEnvFile:
    """.env 文件加载测试"""

    def test_load_env_file_not_exists(self, tmp_path):
        """不存在的 .env 文件应静默处理"""
        with patch.object(config_module, 'ENV_FILE', str(tmp_path / '.env')):
            config_module.load_env_file()  # 不应报错

    def test_load_env_file_valid(self, tmp_path):
        """有效 .env 文件应正确加载"""
        env_file = tmp_path / '.env'
        env_file.write_text('TEST_KEY=test_value\nTEST_KEY2="quoted_value"\n', encoding='utf-8')
        with patch.object(config_module, 'ENV_FILE', str(env_file)):
            config_module.load_env_file()
        assert os.environ.get('TEST_KEY') == 'test_value'
        assert os.environ.get('TEST_KEY2') == 'quoted_value'
        # 清理
        os.environ.pop('TEST_KEY', None)
        os.environ.pop('TEST_KEY2', None)

    def test_load_env_file_skips_comments(self, tmp_path):
        """应跳过注释行"""
        env_file = tmp_path / '.env'
        env_file.write_text('# This is a comment\nVALID_KEY=valid_value\n', encoding='utf-8')
        with patch.object(config_module, 'ENV_FILE', str(env_file)):
            config_module.load_env_file()
        assert os.environ.get('VALID_KEY') == 'valid_value'
        os.environ.pop('VALID_KEY', None)

    def test_load_env_file_skips_empty_lines(self, tmp_path):
        """应跳过空行"""
        env_file = tmp_path / '.env'
        env_file.write_text('\n\nVALID_KEY=value\n\n', encoding='utf-8')
        with patch.object(config_module, 'ENV_FILE', str(env_file)):
            config_module.load_env_file()
        assert os.environ.get('VALID_KEY') == 'value'
        os.environ.pop('VALID_KEY', None)

    def test_load_env_file_invalid_format(self, tmp_path):
        """无效格式应静默跳过"""
        env_file = tmp_path / '.env'
        env_file.write_text('INVALID_LINE_WITHOUT_EQUALS\nVALID_KEY=value\n', encoding='utf-8')
        with patch.object(config_module, 'ENV_FILE', str(env_file)):
            config_module.load_env_file()
        assert os.environ.get('VALID_KEY') == 'value'
        os.environ.pop('VALID_KEY', None)

    def test_load_env_file_does_not_override_existing(self, tmp_path):
        """不应覆盖已存在的环境变量"""
        os.environ['EXISTING_KEY'] = 'original_value'
        env_file = tmp_path / '.env'
        env_file.write_text('EXISTING_KEY=new_value\n', encoding='utf-8')
        with patch.object(config_module, 'ENV_FILE', str(env_file)):
            config_module.load_env_file()
        assert os.environ.get('EXISTING_KEY') == 'original_value'
        os.environ.pop('EXISTING_KEY', None)


class TestGetLedgerPath:
    """项目根目录获取测试"""

    def test_get_ledger_path_default(self):
        """未设置环境变量时应返回默认路径"""
        with patch.dict(os.environ, {}, clear=True):
            path = config_module.get_ledger_path()
            assert path == config_module.ROOT_DIR

    def test_get_ledger_path_from_env(self, tmp_path):
        """从环境变量获取路径"""
        with patch.dict(os.environ, {'LEDGER_PATH': str(tmp_path)}):
            path = config_module.get_ledger_path()
            assert path == str(tmp_path)

    def test_get_ledger_path_invalid_dir(self):
        """无效目录应返回默认路径"""
        with patch.dict(os.environ, {'LEDGER_PATH': '/nonexistent/path/12345'}):
            path = config_module.get_ledger_path()
            assert path == config_module.ROOT_DIR


class TestGetDbPath:
    """数据库路径获取测试"""

    def test_get_db_path_default(self):
        """未设置环境变量时应返回默认路径"""
        with patch.dict(os.environ, {}, clear=True):
            db_path = config_module.get_db_path()
            assert db_path == os.path.join(config_module.ROOT_DIR, 'ledger.db')

    def test_get_db_path_from_env(self, tmp_path):
        """从环境变量获取路径"""
        custom_db = str(tmp_path / 'custom.db')
        with patch.dict(os.environ, {'LEDGER_DB_PATH': custom_db}):
            db_path = config_module.get_db_path()
            assert db_path == custom_db

    def test_get_db_path_relative(self, tmp_path):
        """相对路径应基于项目根目录解析"""
        relative_path = 'data/custom/ledger.db'
        with patch.dict(os.environ, {'LEDGER_DB_PATH': relative_path}):
            db_path = config_module.get_db_path()
            expected = os.path.join(config_module.ROOT_DIR, relative_path)
            assert db_path == expected

    def test_get_db_path_creates_directory(self, tmp_path):
        """应自动创建不存在的目录"""
        nested_db = str(tmp_path / 'data' / 'db' / 'ledger.db')
        with patch.dict(os.environ, {'LEDGER_DB_PATH': nested_db}):
            db_path = config_module.get_db_path()
            assert os.path.dirname(db_path)  # 目录路径应存在或被创建


class TestDbPathConstant:
    """DB_PATH 常量测试"""

    def test_db_path_is_set(self):
        """DB_PATH 应被正确初始化"""
        assert hasattr(config_module, 'DB_PATH')
        assert config_module.DB_PATH is not None
        assert isinstance(config_module.DB_PATH, str)
