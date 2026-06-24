#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""web/agent_routes.py 多套配置 API + /chat config_id 行为测试"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import ledger_modules.agent_config_store as store
from web.agent_routes import register_agent_routes


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / 'test_agent_api.db')
    monkeypatch.setattr(db_module, 'DB_PATH', db_path)
    monkeypatch.setattr(store, 'DB_PATH', db_path)
    db_module.init_db()
    yield db_path


@pytest.fixture
def flask_app():
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True

    def api_error(msg):
        return {'success': False, 'error': msg}

    def api_success(data):
        return {'success': True, 'data': data}

    def sync_db_path():
        pass

    register_agent_routes(app, api_error, api_success, sync_db_path, db_module)
    return app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


# ─── CRUD 端点 ────────────────────────────────

class TestCrudEndpoints:
    def test_list_empty(self, client):
        r = client.get('/api/agent/configs')
        assert r.get_json() == {'success': True, 'data': {'configs': [], 'default_id': None}}

    def test_create(self, client):
        r = client.post('/api/agent/configs', json={
            'name': '默认-DeepSeek',
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'api_key': 'sk-test',
            'is_default': True,
        })
        body = r.get_json()
        assert body['success'] is True
        assert body['data']['id'] > 0
        assert body['data']['is_default'] is True

    def test_create_validation(self, client):
        # 缺 name
        r = client.post('/api/agent/configs', json={'provider': 'p', 'model': 'm'})
        assert r.get_json()['success'] is False
        # 缺 provider
        r = client.post('/api/agent/configs', json={'name': 'n', 'model': 'm'})
        assert r.get_json()['success'] is False
        # 缺 model
        r = client.post('/api/agent/configs', json={'name': 'n', 'provider': 'p'})
        assert r.get_json()['success'] is False

    def test_list_after_create(self, client):
        client.post('/api/agent/configs', json={
            'name': 'A', 'provider': 'deepseek', 'model': 'm', 'is_default': True
        })
        client.post('/api/agent/configs', json={
            'name': 'B', 'provider': 'qwen', 'model': 'm2'
        })
        r = client.get('/api/agent/configs').get_json()
        assert len(r['data']['configs']) == 2
        # 排序按 is_default DESC, updated_at DESC：默认项排第一
        names = [c['name'] for c in r['data']['configs']]
        assert names[0] == 'A'
        # default_id 指向 A
        a_id = next(c['id'] for c in r['data']['configs'] if c['name'] == 'A')
        assert r['data']['default_id'] == a_id

    def test_update(self, client):
        r1 = client.post('/api/agent/configs', json={
            'name': 'A', 'provider': 'deepseek', 'model': 'm', 'is_default': True
        }).get_json()
        cid = r1['data']['id']

        r = client.put(f'/api/agent/configs/{cid}', json={
            'name': 'A-renamed', 'provider': 'deepseek', 'model': 'm',
            'is_enabled': False, 'system_prompt': 'You are a finance helper.'
        })
        body = r.get_json()
        assert body['success'] is True
        assert body['data']['name'] == 'A-renamed'
        assert body['data']['is_enabled'] is False
        assert body['data']['system_prompt'] == 'You are a finance helper.'

    def test_update_not_found(self, client):
        r = client.put('/api/agent/configs/99999', json={
            'name': 'X', 'provider': 'p', 'model': 'm'
        })
        assert r.get_json()['success'] is False
        assert 'not found' in r.get_json()['error']

    def test_delete(self, client):
        r1 = client.post('/api/agent/configs', json={
            'name': 'A', 'provider': 'deepseek', 'model': 'm'
        }).get_json()
        cid = r1['data']['id']

        r = client.delete(f'/api/agent/configs/{cid}')
        assert r.get_json() == {'success': True, 'data': {'deleted': cid}}
        # 删完再 GET 应该少一条
        r = client.get('/api/agent/configs').get_json()
        assert len(r['data']['configs']) == 0

    def test_set_default(self, client):
        r1 = client.post('/api/agent/configs', json={
            'name': 'A', 'provider': 'deepseek', 'model': 'm', 'is_default': True
        }).get_json()
        r2 = client.post('/api/agent/configs', json={
            'name': 'B', 'provider': 'qwen', 'model': 'm'
        }).get_json()

        # 把 B 设为默认
        client.post(f'/api/agent/configs/{r2["data"]["id"]}/set_default')
        listing = client.get('/api/agent/configs').get_json()['data']
        assert listing['default_id'] == r2['data']['id']
        # A 应该不再 is_default
        a = next(c for c in listing['configs'] if c['id'] == r1['data']['id'])
        assert a['is_default'] is False

    def test_legacy_endpoint_still_works(self, client):
        """保留的 POST /api/agent/config 应能创建默认配置。"""
        r = client.post('/api/agent/config', json={
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'api_key': 'sk-test',
        })
        body = r.get_json()
        assert body['success'] is True
        assert body['data']['config']['is_default'] is True

        listing = client.get('/api/agent/configs').get_json()['data']
        assert listing['default_id'] is not None


# ─── /api/agent/chat config_id 行为 ────────────

class TestChatConfigId:
    def test_chat_with_valid_config_id_routes_to_db(self, client):
        """带 config_id 时后端按 DB 内容路由，并发出正确的 provider/model/api_key。"""
        from unittest.mock import patch

        # 先创建一条配置
        r1 = client.post('/api/agent/configs', json={
            'name': 'A', 'provider': 'openai', 'model': 'gpt-4o-mini',
            'api_key': 'sk-from-db', 'is_default': True
        }).get_json()
        cid = r1['data']['id']

        # patch agent_module.agent_service 以避免真实 HTTP 调用
        with patch('ledger_modules.agent.agent_service.load_config') as lc, \
             patch('ledger_modules.agent.agent_service.chat') as chat_mock:
            chat_mock.return_value = {'choices': [{'message': {'content': 'hi'}}]}
            r = client.post('/api/agent/chat', json={
                'message': 'hello', 'config_id': cid,
            })
            body = r.get_json()
            assert body['success'] is True
            # load_config 收到的应是 DB 取出来的内容
            lc.assert_called_once()
            cfg_arg = lc.call_args[0][0]
            assert cfg_arg['provider'] == 'openai'
            assert cfg_arg['model'] == 'gpt-4o-mini'
            assert cfg_arg['api_key'] == 'sk-from-db'

    def test_chat_with_missing_config_id_errors(self, client):
        r = client.post('/api/agent/chat', json={
            'message': 'hello', 'config_id': 99999,
        })
        body = r.get_json()
        assert body['success'] is False
        assert 'not found' in body['error']

    def test_chat_with_inline_config_still_works(self, client):
        """兼容旧前端：不带 config_id 时仍可用内联 config。"""
        from unittest.mock import patch
        with patch('ledger_modules.agent.agent_service.load_config') as lc, \
             patch('ledger_modules.agent.agent_service.chat') as chat_mock:
            chat_mock.return_value = {'choices': [{'message': {'content': 'hi'}}]}
            r = client.post('/api/agent/chat', json={
                'message': 'hello',
                'config': {'provider': 'openai', 'model': 'm', 'api_key': 'k'},
            })
            assert r.get_json()['success'] is True
            lc.assert_called_once_with({
                'provider': 'openai', 'model': 'm', 'api_key': 'k'
            })
