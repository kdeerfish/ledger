"""
Tags & Templates API 集成测试
覆盖新增功能：标签 CRUD、模板 CRUD、交易关联标签、自动建议、增强统计
"""
import json
import os
import sys
import tempfile
import shutil
import sqlite3

import pytest

# 确保项目根目录在 sys.path 中
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)

# ── 先劫持 DB 路径再导入 app ──
TEST_DIR = None
TEST_DB = None


def _setup_test_db():
    global TEST_DIR, TEST_DB
    TEST_DIR = tempfile.mkdtemp()
    TEST_DB = os.path.join(TEST_DIR, "test.db")
    os.environ["LEDGER_DB_PATH"] = TEST_DB
    return TEST_DB


_setup_test_db()

import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module
from web.app import app as flask_app


@pytest.fixture(autouse=True)
def reset_db():
    """每个测试前重置数据库"""
    db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
    db_module.DB_PATH = db_path
    tx_module.DB_PATH = db_path
    budget_module.DB_PATH = db_path

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    tables = ["transactions", "budgets", "budget_templates", "record_templates",
              "transaction_tags", "tags"]
    for t in tables:
        c.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()
    conn.close()

    db_module.init_db()

    import web.app as web_app_module
    web_app_module.DB_PATH = db_path
    web_app_module.sync_db_path()

    yield

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for t in tables:
        c.execute(f"DELETE FROM {t}")
    c.execute("DELETE FROM sqlite_sequence")
    conn.commit()
    conn.close()


@pytest.fixture
def client():
    """Flask 测试客户端"""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ══════════════════════════════════════════════════════════════════════
# Tests
# ══════════════════════════════════════════════════════════════════════

class TestTagsAPI:
    """标签 API 测试"""

    def test_create_tag(self, client):
        resp = client.post('/api/tags', data=json.dumps({"name": "测试标签", "color": "#ef4444"}),
                          content_type='application/json')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert 'id' in data['data']

    def test_create_duplicate_tag(self, client):
        client.post('/api/tags', data=json.dumps({"name": "重复标签"}),
                    content_type='application/json')
        resp = client.post('/api/tags', data=json.dumps({"name": "重复标签"}),
                          content_type='application/json')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True

    def test_list_tags(self, client):
        for name in ["餐饮", "交通", "购物"]:
            client.post('/api/tags', data=json.dumps({"name": name}),
                       content_type='application/json')
        resp = client.get('/api/tags')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert len(data['data']) >= 3
        names = [t['name'] for t in data['data']]
        assert '餐饮' in names

    def test_tag_has_usage_count(self, client):
        resp = client.get('/api/tags')
        data = resp.get_json()
        for tag in data['data']:
            assert 'usage_count' in tag

    def test_delete_tag(self, client):
        resp = client.post('/api/tags', data=json.dumps({"name": "待删除标签"}),
                          content_type='application/json')
        tag_id = resp.get_json()['data']['id']
        resp = client.delete(f'/api/tags/{tag_id}')
        assert resp.status_code == 200
        resp = client.get('/api/tags')
        names = [t['name'] for t in resp.get_json()['data']]
        assert '待删除标签' not in names


class TestTransactionTags:
    """交易关联标签测试"""

    def test_add_transaction_with_tags(self, client):
        tag1 = client.post('/api/tags', data=json.dumps({"name": "午饭"}),
                          content_type='application/json').get_json()['data']['id']
        tag2 = client.post('/api/tags', data=json.dumps({"name": "外卖"}),
                          content_type='application/json').get_json()['data']['id']

        resp = client.post('/api/transactions', data=json.dumps({
            "type": "支出", "amount": 25.0, "category": "食品",
            "account": "微信", "note": "午餐",
            "tag_ids": [tag1, tag2],
            "force": True,
        }), content_type='application/json')
        data = resp.get_json()
        assert resp.status_code == 200
        tx_id = data['data']['id']

        resp = client.get(f'/api/transactions/{tx_id}')
        t = resp.get_json()['data']
        tag_names = [tag['name'] for tag in t['tags']]
        assert '午饭' in tag_names
        assert '外卖' in tag_names

    def test_filter_by_tags(self, client):
        tag = client.post('/api/tags', data=json.dumps({"name": "可筛选标签"}),
                         content_type='application/json').get_json()['data']['id']
        client.post('/api/transactions', data=json.dumps({
            "type": "支出", "amount": 10.0, "category": "测试",
            "tag_ids": [tag], "force": True,
        }), content_type='application/json')

        resp = client.get(f'/api/transactions?tag_ids={tag}')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['data']['total'] >= 1

    def test_update_transaction_tags(self, client):
        tx_resp = client.post('/api/transactions', data=json.dumps({
            "type": "支出", "amount": 30.0, "category": "测试",
            "tag_ids": [], "force": True,
        }), content_type='application/json')
        tx_id = tx_resp.get_json()['data']['id']

        tag = client.post('/api/tags', data=json.dumps({"name": "新标签"}),
                         content_type='application/json').get_json()['data']['id']

        client.put(f'/api/transactions/{tx_id}', data=json.dumps({
            "tag_ids": [tag],
        }), content_type='application/json')

        resp = client.get(f'/api/transactions/{tx_id}')
        tags = resp.get_json()['data']['tags']
        assert len(tags) == 1
        assert tags[0]['name'] == '新标签'


class TestTemplatesAPI:
    """记一笔模板 API 测试"""

    def test_create_template(self, client):
        resp = client.post('/api/templates', data=json.dumps({
            "name": "通勤", "type": "支出", "amount": 5.0,
            "category": "交通", "account": "微信",
            "tag_names": ["日常"],
        }), content_type='application/json')
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'id' in data['data']

    def test_list_templates(self, client):
        client.post('/api/templates', data=json.dumps({
            "name": "午餐", "type": "支出", "amount": 20.0, "category": "食品",
        }), content_type='application/json')
        resp = client.get('/api/templates')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        names = [t['name'] for t in data['data']]
        assert '午餐' in names

    def test_use_template_increments_count(self, client):
        resp = client.post('/api/templates', data=json.dumps({
            "name": "人气模板", "type": "支出", "amount": 15.0, "category": "其他",
        }), content_type='application/json')
        tid = resp.get_json()['data']['id']

        for _ in range(3):
            client.post(f'/api/templates/{tid}/use')
        resp = client.get('/api/templates')
        tmpl = [t for t in resp.get_json()['data'] if t['id'] == tid][0]
        assert tmpl['usage_count'] == 3

    def test_delete_template(self, client):
        resp = client.post('/api/templates', data=json.dumps({
            "name": "待删除模板", "type": "支出", "amount": 99.0,
        }), content_type='application/json')
        tid = resp.get_json()['data']['id']
        client.delete(f'/api/templates/{tid}')
        resp = client.get('/api/templates')
        ids = [t['id'] for t in resp.get_json()['data']]
        assert tid not in ids


class TestSuggestionsAPI:
    """自动建议 API 测试"""

    def test_suggestions_all(self, client):
        resp = client.get('/api/suggestions?field=all')
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'categories' in data['data']
        assert 'accounts' in data['data']
        assert 'members' in data['data']
        assert 'merchants' in data['data']
        assert 'projects' in data['data']
        assert 'frequent' in data['data']

    def test_suggestions_single_field(self, client):
        resp = client.get('/api/suggestions?field=accounts')
        data = resp.get_json()
        assert 'accounts' in data['data']
        assert 'categories' not in data['data']

    def test_suggestions_with_keyword(self, client):
        client.post('/api/transactions', data=json.dumps({
            "type": "支出", "amount": 1.0, "merchant": "测试商家专用",
            "force": True,
        }), content_type='application/json')
        resp = client.get('/api/suggestions?field=merchants&keyword=测试')
        data = resp.get_json()
        names = [m['name'] for m in data['data']['merchants']]
        assert '测试商家专用' in names


class TestEnhancedStats:
    """增强统计 API 测试"""

    def test_stats_by_tag(self, client):
        tag = client.post('/api/tags', data=json.dumps({"name": "统计标签"}),
                         content_type='application/json').get_json()['data']['id']
        client.post('/api/transactions', data=json.dumps({
            "type": "支出", "amount": 50.0, "tag_ids": [tag], "force": True,
        }), content_type='application/json')
        resp = client.get('/api/stats?group_by=tag')
        data = resp.get_json()
        assert resp.status_code == 200
        groups = [i['group'] for i in data['data']['items']]
        assert '统计标签' in groups

    def test_stats_by_merchant(self, client):
        resp = client.get('/api/stats?group_by=merchant')
        assert resp.status_code == 200

    def test_stats_by_project(self, client):
        resp = client.get('/api/stats?group_by=project')
        assert resp.status_code == 200

    def test_stats_by_member(self, client):
        resp = client.get('/api/stats?group_by=member')
        assert resp.status_code == 200

    def test_trends_api(self, client):
        resp = client.get('/api/trends?year=2026&granularity=month')
        data = resp.get_json()
        assert resp.status_code == 200
        assert 'items' in data['data']
        assert 'cumulative' in data['data']

    def test_type_stats(self, client):
        resp = client.get('/api/stats?group_by=type')
        assert resp.status_code == 200

    def test_subcategory_stats(self, client):
        resp = client.get('/api/stats?group_by=subcategory')
        assert resp.status_code == 200


class TestQuickCategories:
    """常用子类别 API 测试"""

    def test_quick_categories(self, client):
        resp = client.get('/api/categories/quick')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        if data['data']:
            assert 'category' in data['data'][0]
            assert 'subcategory' in data['data'][0]
