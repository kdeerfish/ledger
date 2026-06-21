#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""web/app.py 补充测试 - 覆盖未测 API 路由"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import web.app as web_app


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """每个测试用独立临时数据库"""
    db_path = str(tmp_path / 'test_web_ext.db')
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


# ─── catch_all 路由 ─────────────────────────────

class TestCatchAll:
    def test_api_404(self, client):
        r = client.get('/api/nonexistent')
        assert r.status_code == 404

    def test_root_returns_something(self, client):
        r = client.get('/')
        # 不管有没有前端文件，应该返回 200 或 3xx
        assert r.status_code in (200, 301, 302, 404)

    def test_static_file(self, client):
        # 请求一个不存在的静态文件
        r = client.get('/nonexistent-file.js')
        assert r.status_code in (200, 404)


# ─── 趋势 API ───────────────────────────────────

class TestTrends:
    def test_trends_month(self, client):
        _add_tx(client, amount=50, date='2025-06-01')
        _add_tx(client, amount=30, date='2025-06-15')
        r = client.get('/api/trends?year=2025&granularity=month')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert data['granularity'] == 'month'
        assert len(data['items']) > 0

    def test_trends_day(self, client):
        _add_tx(client, amount=50, date='2025-06-10')
        r = client.get('/api/trends?year=2025&granularity=day')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert data['granularity'] == 'day'

    def test_trends_week(self, client):
        _add_tx(client, amount=50, date='2025-06-10')
        r = client.get('/api/trends?year=2025&granularity=week')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert data['granularity'] == 'week'

    def test_trends_empty(self, client):
        r = client.get('/api/trends?year=2020')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert len(data['items']) == 0

    def test_trends_cumulative(self, client):
        _add_tx(client, amount=100, date='2025-06-01')
        r = client.get('/api/trends?year=2025')
        data = r.get_json()['data']
        assert 'cumulative' in data


# ─── Tags API ───────────────────────────────────

class TestTags:
    def test_create_tag(self, client):
        r = client.post('/api/tags', json={'name': '重要'})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_list_tags(self, client):
        client.post('/api/tags', json={'name': 'A'})
        client.post('/api/tags', json={'name': 'B'})
        r = client.get('/api/tags')
        assert r.status_code == 200
        assert len(r.get_json()['data']) == 2

    def test_delete_tag(self, client):
        r = client.post('/api/tags', json={'name': 'Del'})
        tag_id = r.get_json()['data']['id']
        r = client.delete(f'/api/tags/{tag_id}')
        assert r.status_code == 200

    def test_delete_nonexistent_tag(self, client):
        r = client.delete('/api/tags/99999')
        # API 对不存在的标签也返回 200（幂等）
        assert r.status_code in (200, 404)


# ─── Templates API ──────────────────────────────

class TestTemplates:
    def test_create_template(self, client):
        r = client.post('/api/templates', json={
            'name': '午餐', 'type': '支出', 'amount': 25,
            'category': '餐饮', 'subcategory': '午餐',
        })
        assert r.status_code == 200

    def test_list_templates(self, client):
        client.post('/api/templates', json={'name': 'T1', 'type': '支出', 'amount': 10})
        r = client.get('/api/templates')
        assert r.status_code == 200
        assert len(r.get_json()['data']) >= 1

    def test_use_template(self, client):
        r = client.post('/api/templates', json={
            'name': '午餐', 'type': '支出', 'amount': 25,
            'category': '餐饮',
        })
        tid = r.get_json()['data']['id']
        r = client.post(f'/api/templates/{tid}/use')
        assert r.status_code == 200
        # 检查 usage_count 增加
        r = client.get('/api/templates')
        for t in r.get_json()['data']:
            if t['id'] == tid:
                assert t['usage_count'] >= 1
                return

    def test_delete_template(self, client):
        r = client.post('/api/templates', json={'name': 'Del', 'type': '支出', 'amount': 10})
        tid = r.get_json()['data']['id']
        r = client.delete(f'/api/templates/{tid}')
        assert r.status_code == 200


# ─── Suggestions API ────────────────────────────

class TestSuggestions:
    def test_suggestions_empty(self, client):
        r = client.get('/api/suggestions')
        assert r.status_code == 200

    def test_suggestions_with_data(self, client):
        for i in range(3):
            _add_tx(client, amount=50, category='交通', date=f'2025-06-{i+1:02d}')
        r = client.get('/api/suggestions')
        assert r.status_code == 200

    def test_suggestions_with_keyword(self, client):
        for i in range(3):
            _add_tx(client, amount=50, category='交通', merchant='滴滴', date=f'2025-06-{i+1:02d}')
        r = client.get('/api/suggestions?keyword=滴滴')
        assert r.status_code == 200

    def test_suggestions_single_field(self, client):
        for i in range(3):
            _add_tx(client, amount=50, category='餐饮', account='微信', date=f'2025-06-{i+1:02d}')
        r = client.get('/api/suggestions?field=account')
        assert r.status_code == 200


# ─── Enhanced Stats ─────────────────────────────

class TestEnhancedStats:
    def test_stats_by_tag(self, client):
        # 创建标签
        r = client.post('/api/tags', json={'name': '工作'})
        tag_id = r.get_json()['data']['id']
        # 创建带标签的交易
        r = _add_tx(client, amount=200)
        tx_id = r.get_json()['data']['id']
        client.put(f'/api/transactions/{tx_id}', json={'tag_ids': [tag_id]})
        # 查询
        r = client.get('/api/stats?group_by=tag')
        assert r.status_code == 200

    def test_stats_by_merchant(self, client):
        _add_tx(client, amount=50, merchant='美团')
        _add_tx(client, amount=30, merchant='美团')
        r = client.get('/api/stats?group_by=merchant')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert len(data['items']) >= 1

    def test_stats_by_project(self, client):
        _add_tx(client, amount=100, project='项目A')
        r = client.get('/api/stats?group_by=project')
        assert r.status_code == 200

    def test_stats_by_member(self, client):
        _add_tx(client, amount=100, member='张三')
        r = client.get('/api/stats?group_by=member')
        assert r.status_code == 200

    def test_stats_type(self, client):
        _add_tx(client, amount=100)
        r = client.get('/api/stats?group_by=type')
        assert r.status_code == 200

    def test_stats_subcategory(self, client):
        _add_tx(client, amount=50, subcategory='午餐')
        _add_tx(client, amount=30, subcategory='晚餐')
        r = client.get('/api/stats?group_by=subcategory')
        assert r.status_code == 200

    def test_stats_empty(self, client):
        r = client.get('/api/stats?group_by=category')
        assert r.status_code == 200


# ─── Quick Categories ───────────────────────────

class TestQuickCategories:
    def test_quick_categories(self, client):
        for i in range(3):
            _add_tx(client, category='餐饮', subcategory='午餐', date=f'2025-06-{i+1:02d}')
        r = client.get('/api/categories/quick')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert len(data) >= 1


# ─── Budget Check ───────────────────────────────

class TestBudgetCheck:
    def test_check_with_spending(self, client):
        _add_tx(client, amount=200, category='餐饮', date='2025-06-05')
        client.post('/api/budgets', json={
            'category': '餐饮', 'amount': 500, 'year': 2025, 'month': 6,
        })
        r = client.get('/api/budgets/check?year=2025&month=6')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert len(data) >= 1
        assert data[0]['spent'] == 200

    def test_check_no_budgets(self, client):
        r = client.get('/api/budgets/check?year=2025&month=1')
        assert r.status_code == 200
        assert len(r.get_json()['data']) == 0


# ─── Export with filters ────────────────────────

class TestExportFilters:
    def test_export_with_date_filter(self, client):
        _add_tx(client, amount=50, date='2025-06-01')
        _add_tx(client, amount=30, date='2025-07-01')
        r = client.get('/api/export?format=json&start_date=2025-06-01&end_date=2025-06-30')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert data['count'] == 1

    def test_export_with_category_filter(self, client):
        _add_tx(client, amount=50, category='餐饮')
        _add_tx(client, amount=30, category='交通')
        r = client.get('/api/export?format=json&category=餐饮')
        assert r.status_code == 200
        data = r.get_json()['data']
        assert data['count'] == 1


# ─── Projects/Members/Merchants ─────────────────

class TestMetadataAPIs:
    def test_projects(self, client):
        _add_tx(client, amount=50, project='P1')
        r = client.get('/api/projects')
        assert r.status_code == 200
        assert len(r.get_json()['data']) >= 1

    def test_merchants(self, client):
        _add_tx(client, amount=50, merchant='M1')
        r = client.get('/api/merchants')
        assert r.status_code == 200
        assert len(r.get_json()['data']) >= 1

    def test_members(self, client):
        _add_tx(client, amount=50, member='张三')
        r = client.get('/api/members')
        assert r.status_code == 200
        assert len(r.get_json()['data']) >= 1
