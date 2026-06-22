#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_method 覆盖中间件测试 - 验证 wget 兼容性"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import web.app as web_app


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """每个测试用独立临时数据库"""
    db_path = str(tmp_path / 'test_method.db')
    monkeypatch.setattr(db_module, 'DB_PATH', db_path)
    monkeypatch.setattr(web_app, 'DB_PATH', db_path)
    db_module.init_db()
    yield db_path


@pytest.fixture
def client():
    web_app.app.config['TESTING'] = True
    with web_app.app.test_client() as c:
        yield c


def _add_tx(client, **kwargs):
    data = {
        'type': '支出', 'amount': 100, 'category': '餐饮',
        'subcategory': '午餐', 'account': '支付宝', 'date': '2025-06-01',
    }
    data.update(kwargs)
    return client.post('/api/transactions', json=data)


# ══════════════════════════════════════════════════════
# 交易 PUT via _method
# ══════════════════════════════════════════════════════

class TestMethodOverrideTransactionPut:
    """POST + ?_method=PUT 应等价于 PUT"""

    def test_put_single_field(self, client):
        """单字段修改：金额"""
        r = _add_tx(client, amount=100)
        tid = r.get_json()['data']['id']

        r = client.post(
            f'/api/transactions/{tid}?_method=PUT',
            json={'field': 'amount', 'value': 200},
        )
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # 验证确实改了
        r = client.get(f'/api/transactions/{tid}')
        assert r.get_json()['data']['amount'] == 200.0

    def test_put_multi_field(self, client):
        """多字段修改"""
        r = _add_tx(client, amount=50, category='餐饮', note='午餐')
        tid = r.get_json()['data']['id']

        r = client.post(
            f'/api/transactions/{tid}?_method=PUT',
            json={'amount': 88, 'note': '晚餐', 'category': '外卖'},
        )
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        r = client.get(f'/api/transactions/{tid}')
        data = r.get_json()['data']
        assert data['amount'] == 88.0
        assert data['note'] == '晚餐'
        assert data['category'] == '外卖'

    def test_put_updates_category(self, client):
        """修改类别"""
        r = _add_tx(client, category='餐饮')
        tid = r.get_json()['data']['id']

        r = client.post(
            f'/api/transactions/{tid}?_method=PUT',
            json={'category': '交通'},
        )
        assert r.status_code == 200

        r = client.get(f'/api/transactions/{tid}')
        assert r.get_json()['data']['category'] == '交通'


# ══════════════════════════════════════════════════════
# 交易 DELETE via _method
# ══════════════════════════════════════════════════════

class TestMethodOverrideTransactionDelete:
    """POST + ?_method=DELETE 应等价于 DELETE"""

    def test_delete_transaction(self, client):
        r = _add_tx(client)
        tid = r.get_json()['data']['id']

        r = client.post(f'/api/transactions/{tid}?_method=DELETE')
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # 软删除：查不到（默认不包含已删除）
        r = client.get('/api/transactions?limit=100')
        ids = [t['id'] for t in r.get_json()['data']['transactions']]
        assert tid not in ids

    def test_delete_then_restore(self, client):
        """删除后可通过 restore 恢复"""
        r = _add_tx(client)
        tid = r.get_json()['data']['id']

        # 删除
        client.post(f'/api/transactions/{tid}?_method=DELETE')

        # 恢复
        r = client.post(f'/api/transactions/{tid}/restore')
        assert r.status_code == 200

        # 又能查到了
        r = client.get(f'/api/transactions/{tid}')
        assert r.status_code == 200


# ══════════════════════════════════════════════════════
# 模板 PUT / DELETE via _method
# ══════════════════════════════════════════════════════

class TestMethodOverrideTemplate:
    """模板的 PUT / DELETE _method 覆盖"""

    def _create_template(self, client):
        r = client.post('/api/templates', json={
            'name': '早餐模板', 'template_type': '日常',
            'type': '支出', 'amount': 15,
            'category': '食品酒水', 'subcategory': '早餐',
            'account': '微信零钱',
        })
        return r.get_json()['data']['id']

    def test_put_template(self, client):
        tid = self._create_template(client)

        r = client.post(
            f'/api/templates/{tid}?_method=PUT',
            json={'amount': 20, 'name': '早餐模板v2'},
        )
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # 验证
        r = client.get('/api/templates')
        templates = r.get_json()['data']
        t = next(x for x in templates if x['id'] == tid)
        assert t['amount'] == 20
        assert t['name'] == '早餐模板v2'

    def test_delete_template(self, client):
        tid = self._create_template(client)

        r = client.post(f'/api/templates/{tid}?_method=DELETE')
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # 验证已删除
        r = client.get('/api/templates')
        ids = [x['id'] for x in r.get_json()['data']]
        assert tid not in ids


# ══════════════════════════════════════════════════════
# 标签 DELETE via _method
# ══════════════════════════════════════════════════════

class TestMethodOverrideTag:
    """标签的 DELETE _method 覆盖"""

    def test_delete_tag(self, client):
        r = client.post('/api/tags', json={'name': '报销', 'color': '#ef4444'})
        tag_id = r.get_json()['data']['id']

        r = client.post(f'/api/tags/{tag_id}?_method=DELETE')
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # 验证已删除
        r = client.get('/api/tags')
        ids = [x['id'] for x in r.get_json()['data']]
        assert tag_id not in ids


# ══════════════════════════════════════════════════════
# 原始方法不受影响
# ══════════════════════════════════════════════════════

class TestOriginalMethodsIntact:
    """确保原始 PUT / DELETE 不受中间件影响"""

    def test_original_put(self, client):
        r = _add_tx(client, amount=100)
        tid = r.get_json()['data']['id']

        r = client.put(
            f'/api/transactions/{tid}',
            json={'amount': 999},
        )
        assert r.status_code == 200

        r = client.get(f'/api/transactions/{tid}')
        assert r.get_json()['data']['amount'] == 999.0

    def test_original_delete(self, client):
        r = _add_tx(client)
        tid = r.get_json()['data']['id']

        r = client.delete(f'/api/transactions/{tid}')
        assert r.status_code == 200

    def test_post_without_method_still_works(self, client):
        """普通 POST 不被 _method 影响"""
        r = client.post('/api/transactions', json={
            'type': '支出', 'amount': 10, 'category': '测试',
        })
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_post_with_invalid_method_ignored(self, client):
        """无效的 _method 值应被忽略，请求仍是 POST"""
        r = _add_tx(client, amount=100)
        tid = r.get_json()['data']['id']

        # _method=INVALID 应被忽略，仍是 POST → 找不到 POST handler → 405
        r = client.post(
            f'/api/transactions/{tid}?_method=INVALID',
            json={'amount': 200},
        )
        assert r.status_code == 405


# ══════════════════════════════════════════════════════
# 边界情况
# ══════════════════════════════════════════════════════

class TestMethodOverrideEdgeCases:
    """边界情况"""

    def test_case_insensitive(self, client):
        """_method 值大小写不敏感"""
        r = _add_tx(client, amount=100)
        tid = r.get_json()['data']['id']

        r = client.post(
            f'/api/transactions/{tid}?_method=put',
            json={'amount': 111},
        )
        assert r.status_code == 200

        r = client.get(f'/api/transactions/{tid}')
        assert r.get_json()['data']['amount'] == 111.0

    def test_patch_method(self, client):
        """_method=PATCH 也应生效"""
        r = _add_tx(client, amount=100)
        tid = r.get_json()['data']['id']

        r = client.post(
            f'/api/transactions/{tid}?_method=PATCH',
            json={'amount': 222},
        )
        # PATCH 路由未注册，应返回 405
        assert r.status_code == 405
