#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger_modules.agent_config_store 测试"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import ledger_modules.agent_config_store as store


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / 'test_agent_cfg.db')
    monkeypatch.setattr(db_module, 'DB_PATH', db_path)
    monkeypatch.setattr(store, 'DB_PATH', db_path)
    db_module.init_db()
    yield db_path


# ─── 基础 CRUD ─────────────────────────────────

class TestBasicCRUD:
    def test_create_and_get(self):
        cfg = store.create_config(
            user_id=None, name='默认-DeepSeek', provider='deepseek',
            model='deepseek-chat', api_key='sk-test', is_default=True,
        )
        assert cfg['id'] > 0
        assert cfg['name'] == '默认-DeepSeek'
        assert cfg['provider'] == 'deepseek'
        assert cfg['is_default'] is True
        assert cfg['is_enabled'] is True

        fetched = store.get_config(cfg['id'], None)
        assert fetched['id'] == cfg['id']
        assert fetched['api_key'] == 'sk-test'

    def test_list_configs(self):
        store.create_config(None, 'A', 'deepseek', 'm1', 'k1')
        store.create_config(None, 'B', 'qwen', 'm2', 'k2')
        rows = store.list_configs(None)
        assert len(rows) == 2

    def test_list_user_isolation(self):
        store.create_config(user_id=1, name='u1', provider='p', model='m', api_key='k')
        store.create_config(user_id=2, name='u2', provider='p', model='m', api_key='k')
        store.create_config(user_id=None, name='g', provider='p', model='m', api_key='k')

        assert len(store.list_configs(1)) == 1
        assert len(store.list_configs(2)) == 1
        assert len(store.list_configs(None)) == 1
        assert len(store.list_configs(999)) == 0

    def test_update(self):
        cfg = store.create_config(None, 'A', 'deepseek', 'm', 'k')
        updated = store.update_config(
            cfg['id'], None, name='A2', provider='qwen', model='m2',
            api_key='k2', is_enabled=False,
        )
        assert updated['name'] == 'A2'
        assert updated['provider'] == 'qwen'
        assert updated['is_enabled'] is False

    def test_update_wrong_user_returns_none(self):
        cfg = store.create_config(user_id=1, name='u1', provider='p', model='m', api_key='k')
        result = store.update_config(cfg['id'], None, name='hijack', provider='x', model='y', api_key='z')
        assert result is None

    def test_delete(self):
        cfg = store.create_config(None, 'A', 'p', 'm', 'k')
        assert store.delete_config(cfg['id'], None) is True
        assert store.get_config(cfg['id'], None) is None

    def test_delete_wrong_user_returns_false(self):
        cfg = store.create_config(user_id=1, name='u1', provider='p', model='m', api_key='k')
        assert store.delete_config(cfg['id'], None) is False
        assert store.delete_config(cfg['id'], 2) is False
        assert store.delete_config(cfg['id'], 1) is True


# ─── 默认配置不变量 ─────────────────────────────

class TestDefaultUniqueness:
    def test_create_default_clears_others(self):
        a = store.create_config(None, 'A', 'p', 'm1', 'k', is_default=True)
        b = store.create_config(None, 'B', 'p', 'm2', 'k', is_default=True)
        rows = store.list_configs(None)
        defaults = [r for r in rows if r['is_default']]
        assert len(defaults) == 1
        assert defaults[0]['id'] == b['id']

    def test_set_default_clears_others(self):
        a = store.create_config(None, 'A', 'p', 'm1', 'k', is_default=True)
        b = store.create_config(None, 'B', 'p', 'm2', 'k')
        c = store.create_config(None, 'C', 'p', 'm3', 'k')

        store.set_default(c['id'], None)

        defaults = [r for r in store.list_configs(None) if r['is_default']]
        assert len(defaults) == 1
        assert defaults[0]['id'] == c['id']

    def test_per_user_default_independent(self):
        u1 = store.create_config(user_id=1, name='u1', provider='p', model='m', api_key='k', is_default=True)
        u2 = store.create_config(user_id=2, name='u2', provider='p', model='m', api_key='k', is_default=True)
        # 设置 user=1 的另一条为默认，不应影响 user=2
        u1b = store.create_config(user_id=1, name='u1b', provider='p', model='m', api_key='k')
        store.set_default(u1b['id'], 1)

        u1_defaults = [r for r in store.list_configs(1) if r['is_default']]
        u2_defaults = [r for r in store.list_configs(2) if r['is_default']]
        assert len(u1_defaults) == 1 and u1_defaults[0]['id'] == u1b['id']
        assert len(u2_defaults) == 1 and u2_defaults[0]['id'] == u2['id']

    def test_set_default_wrong_user_returns_none(self):
        cfg = store.create_config(user_id=1, name='u1', provider='p', model='m', api_key='k')
        assert store.set_default(cfg['id'], 999) is None


# ─── get_default_config ─────────────────────────

class TestGetDefault:
    def test_picks_default_when_present(self):
        a = store.create_config(None, 'A', 'p', 'm', 'k')
        b = store.create_config(None, 'B', 'p', 'm', 'k', is_default=True)
        d = store.get_default_config(None)
        assert d['id'] == b['id']

    def test_falls_back_to_newest_enabled(self):
        store.create_config(None, 'A', 'p', 'm1', 'k')
        b = store.create_config(None, 'B', 'p', 'm2', 'k')
        d = store.get_default_config(None)
        assert d['id'] == b['id']

    def test_returns_none_when_empty(self):
        assert store.get_default_config(None) is None
