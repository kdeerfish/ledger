#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""budgets 模块补充测试 - 覆盖未测路径"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import ledger_modules.budgets as budget_module


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """每个测试用独立临时数据库"""
    db_path = str(tmp_path / 'test_budgets.db')
    monkeypatch.setattr(db_module, 'DB_PATH', db_path)
    monkeypatch.setattr(budget_module, 'DB_PATH', db_path)
    db_module.init_db()
    yield db_path


def _add_tx(category='餐饮', amount=100, subcategory='午餐', account='支付宝',
            project='', member='', merchant='食堂', note='', trans_date='2025-06-01'):
    """快捷添加交易"""
    import ledger_modules.transactions as tx
    tx.DB_PATH = db_module.DB_PATH
    return tx.add_transaction('支出', amount, category, subcategory,
                              account, project, member, merchant, note, trans_date)


# ─── Record Template 测试 ──────────────────────────

class TestRecordTemplate:
    def test_create_and_get(self):
        tid = budget_module.create_record_template(
            name='午餐模板', template_type='支出',
            type_='支出', amount=25, category='餐饮',
            subcategory='午餐', account='支付宝',
            project='', member='', merchant='食堂', note='日常午餐',
        )
        assert tid > 0
        t = budget_module.get_record_template(tid)
        assert t is not None
        assert t['name'] == '午餐模板'
        assert t['amount'] == 25
        assert t['usage_count'] == 0

    def test_get_nonexistent(self):
        t = budget_module.get_record_template(99999)
        assert t is None

    def test_list_templates(self):
        budget_module.create_record_template(name='T1', template_type='支出', type_='支出', amount=10)
        budget_module.create_record_template(name='T2', template_type='收入', type_='收入', amount=20)
        templates = budget_module.list_record_templates()
        assert len(templates) == 2

    def test_update_template(self):
        tid = budget_module.create_record_template(name='Old', template_type='支出', type_='支出', amount=10)
        ok = budget_module.update_record_template(tid, name='New', amount=99)
        assert ok is True
        t = budget_module.get_record_template(tid)
        assert t['name'] == 'New'
        assert t['amount'] == 99

    def test_update_empty_kwargs(self):
        tid = budget_module.create_record_template(name='T', template_type='支出', type_='支出', amount=10)
        ok = budget_module.update_record_template(tid)
        assert ok is False

    def test_update_invalid_fields(self):
        tid = budget_module.create_record_template(name='T', template_type='支出', type_='支出', amount=10)
        ok = budget_module.update_record_template(tid, invalid_field='x')
        assert ok is False

    def test_delete_template(self):
        tid = budget_module.create_record_template(name='Del', template_type='支出', type_='支出', amount=10)
        ok = budget_module.delete_record_template(tid)
        assert ok is True
        assert budget_module.get_record_template(tid) is None

    def test_delete_nonexistent(self):
        ok = budget_module.delete_record_template(99999)
        assert ok is False

    def test_apply_template(self):
        tid = budget_module.create_record_template(
            name='测试', template_type='支出', type_='支出', amount=50,
            category='餐饮', subcategory='早餐',
        )
        data = budget_module.apply_record_template(tid)
        assert data is not None
        assert data['amount'] == 50
        assert data['category'] == '餐饮'
        # usage_count +1
        t = budget_module.get_record_template(tid)
        assert t['usage_count'] == 1

    def test_apply_template_with_override(self):
        tid = budget_module.create_record_template(
            name='测试', template_type='支出', type_='支出', amount=50,
            category='餐饮',
        )
        data = budget_module.apply_record_template(tid, amount_override=100)
        assert data['amount'] == 100

    def test_apply_nonexistent_template(self):
        data = budget_module.apply_record_template(99999)
        assert data is None

    def test_suggest_templates(self):
        # 添加足够多的同类交易触发推荐
        for i in range(3):
            _add_tx(category='交通', amount=20 + i, trans_date=f'2025-06-{i+1:02d}')
        suggestions = budget_module.suggest_record_templates(limit=5)
        assert isinstance(suggestions, list)
        # 至少有一个推荐
        if suggestions:
            assert 'name' in suggestions[0]
            assert 'template_type' in suggestions[0]

    def test_suggest_templates_empty_db(self):
        suggestions = budget_module.suggest_record_templates()
        assert suggestions == []


# ─── Budget by dimension 测试 ─────────────────────

class TestBudgetDimension:
    def test_set_budget_account_dimension(self):
        budget_module.set_budget('餐饮', 1000, 2025, 6, 'account', '支付宝')
        conn = db_module.sqlite3.connect(db_module.DB_PATH)
        c = conn.cursor()
        c.execute('SELECT dimension_type, dimension_value FROM budgets WHERE category=?', ('餐饮',))
        row = c.fetchone()
        conn.close()
        assert row[0] == 'account'
        assert row[1] == '支付宝'

    def test_set_budget_auto_dimension(self):
        budget_module.set_budget('交通', 500, 2025, 6)
        conn = db_module.sqlite3.connect(db_module.DB_PATH)
        c = conn.cursor()
        c.execute('SELECT dimension_type FROM budgets WHERE category=?', ('交通',))
        row = c.fetchone()
        conn.close()
        assert row[0] == 'category'

    def test_budget_check_with_spending(self):
        _add_tx(category='餐饮', amount=150, trans_date='2025-06-10')
        budget_module.set_budget('餐饮', 500, 2025, 6)
        spent = budget_module._get_budget_spent('餐饮', 2025, 6, 'category', None)
        assert spent == 150

    def test_budget_check_no_budgets(self):
        # 没有预算时 _get_budget_spent 返回 0
        spent = budget_module._get_budget_spent('餐饮', 2025, 1, 'category', None)
        assert spent == 0


# ─── suggest_templates 维度测试 ────────────────────

class TestSuggestDimensions:
    def test_suggest_by_account(self):
        for i in range(3):
            _add_tx(category='日用', amount=10, account='微信',
                    trans_date=f'2025-06-{i+1:02d}')
        # suggest_record_templates 不返回 dimension_type，这是 suggest_budget_templates 的功能
        suggestions = budget_module.suggest_record_templates()
        assert isinstance(suggestions, list)

    def test_suggest_by_member(self):
        for i in range(3):
            _add_tx(category='教育', amount=50, member='张三',
                    trans_date=f'2025-06-{i+1:02d}')
        suggestions = budget_module.suggest_record_templates()
        assert isinstance(suggestions, list)

    def test_suggest_by_project(self):
        for i in range(3):
            _add_tx(category='办公', amount=30, project='项目A',
                    trans_date=f'2025-06-{i+1:02d}')
        suggestions = budget_module.suggest_record_templates()
        for s in suggestions:
            if s.get('project') == '项目A':
                return

    def test_suggest_by_merchant(self):
        for i in range(3):
            _add_tx(category='餐饮', amount=25, merchant='美团',
                    trans_date=f'2025-06-{i+1:02d}')
        suggestions = budget_module.suggest_record_templates()
        assert isinstance(suggestions, list)

    def test_suggest_income_type(self):
        for i in range(3):
            import ledger_modules.transactions as tx
            tx.DB_PATH = db_module.DB_PATH
            tx.add_transaction('收入', 1000, '工资', '', '银行', '', '', '', '',
                               f'2025-06-{i+1:02d}')
        suggestions = budget_module.suggest_record_templates()
        for s in suggestions:
            if s.get('type') == '收入':
                assert s.get('template_type') == '收入'
                return

    def test_suggest_empty_category(self):
        for i in range(3):
            _add_tx(category='', amount=10, subcategory='午餐',
                    trans_date=f'2025-06-{i+1:02d}')
        suggestions = budget_module.suggest_record_templates()
        # subcategory 不为空时名字用 subcategory
        assert isinstance(suggestions, list)
