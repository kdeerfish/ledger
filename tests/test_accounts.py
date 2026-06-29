#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账户管理、双账户交易、余额计算测试
"""

import os
import sys
import pytest
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.import_engine as import_engine


class TestAccountCRUD:
    """账户管理基础操作测试"""

    def test_create_account(self, temp_db):
        aid = db_module.create_account('微信', 'self', '', '', 1000)
        assert aid is not None

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT name, account_type, opening_balance FROM accounts WHERE id=?', (aid,))
        row = c.fetchone()
        conn.close()
        assert row[0] == '微信'
        assert row[1] == 'self'
        assert row[2] == 1000.0

    def test_create_duplicate_account_returns_existing_id(self, temp_db):
        aid1 = db_module.create_account('支付宝', 'self', '', '', 500)
        aid2 = db_module.create_account('支付宝', 'self', '', '', 500)
        assert aid1 == aid2

    def test_get_account_by_name(self, temp_db):
        db_module.create_account('银行卡', 'self', '', '', 2000)
        acc = db_module.get_account_by_name('银行卡')
        assert acc is not None
        assert acc['account_type'] == 'self'
        assert acc['opening_balance'] == 2000

    def test_get_account_by_name_missing(self, temp_db):
        assert db_module.get_account_by_name('不存在的账户') is None

    def test_update_account(self, temp_db):
        aid = db_module.create_account('现金', 'self', '', '', 100)
        ok = db_module.update_account(aid, name='现金(美元)', opening_balance=200)
        assert ok is True

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT name, opening_balance FROM accounts WHERE id=?', (aid,))
        row = c.fetchone()
        conn.close()
        assert row[0] == '现金(美元)'
        assert row[1] == 200.0

    def test_delete_account(self, temp_db):
        aid = db_module.create_account('临时账户', 'self', '', '', 0)
        ok = db_module.delete_account(aid)
        assert ok is True

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM accounts WHERE id=?', (aid,))
        assert c.fetchone()[0] == 0
        conn.close()


class TestAccountBalances:
    """账户余额与净资产测试"""

    def test_balance_with_opening_balance(self, temp_db):
        db_module.create_account('微信', 'self', '', '', 1000)
        tx_module.add_transaction('支出', 100, '餐饮', '', '微信', '', '', '', '午饭', from_account='微信', to_account='商户A', ensure_accounts=False)
        tx_module.add_transaction('收入', 500, '退款', '', '微信', '', '', '', '退款', from_account='商户B', to_account='微信', ensure_accounts=False)

        balances = tx_module.get_account_balances_with_type()
        wechat = next(b for b in balances if b['name'] == '微信')
        assert wechat['balance'] == 1400.0
        assert wechat['opening_balance'] == 1000.0
        assert wechat['transaction_balance'] == 400.0

    def test_claims_and_liability_in_net_worth(self, temp_db):
        db_module.create_account('微信', 'self', '', '', 1000)
        db_module.create_account('张三', 'claims', '张三', '微信', 0)
        db_module.create_account('招商银行信用卡', 'liability', '', '', 0)

        tx_module.add_transaction('债权变更', 500, '借出', '', '微信', '', '张三', '', '借给张三', from_account='微信', to_account='张三', ensure_accounts=False)
        tx_module.add_transaction('负债变更', 2000, '还信用卡', '', '微信', '', '招商银行信用卡', '', '还信用卡', from_account='微信', to_account='招商银行信用卡', ensure_accounts=False)

        balances = tx_module.get_account_balances_with_type()
        wechat = next(b for b in balances if b['name'] == '微信')
        claims = next(b for b in balances if b['name'] == '张三')
        liability = next(b for b in balances if b['name'] == '招商银行信用卡')

        assert wechat['balance'] == -1500.0
        assert claims['balance'] == 500.0
        assert liability['balance'] == 2000.0

        net = tx_module.get_net_worth()
        assert net == -1500.0 + 500.0 - 2000.0

    def test_negative_balance_is_allowed(self, temp_db):
        db_module.create_account('测试账户', 'self', '', '', 0)
        tx_module.add_transaction('支出', 10, '测试', '', '测试账户', '', '', '', '', from_account='测试账户', to_account='商户', ensure_accounts=False)
        tx_module.add_transaction('支出', 20, '测试', '', '测试账户', '', '', '', '', from_account='测试账户', to_account='商户', ensure_accounts=False)

        balances = tx_module.get_account_balances_with_type()
        assert next(b for b in balances if b['name'] == '测试账户')['balance'] == -30.0


class TestDualAccountTransactions:
    """双账户交易测试"""

    def test_add_transaction_sets_dual_accounts(self, temp_db):
        tx_module.add_transaction('转账', 1000, '转账', '', '微信', '', '', '', '', from_account='微信', to_account='支付宝', ensure_accounts=False)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT from_account, to_account FROM transactions WHERE id=1')
        row = c.fetchone()
        conn.close()
        assert row[0] == '微信'
        assert row[1] == '支付宝'

    def test_list_transactions_filters_by_dual_accounts(self, temp_db):
        tx_module.add_transaction('转账', 100, '转账', '', '微信', '', '', '', '', from_account='微信', to_account='支付宝', ensure_accounts=False)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT count(*) FROM transactions WHERE from_account=? AND to_account=?', ('微信', '支付宝'))
        assert c.fetchone()[0] == 1
        conn.close()

    def test_search_includes_dual_accounts(self, temp_db):
        tx_module.add_transaction('支出', 50, '餐饮', '', '微信', '', '', '', '', from_account='微信', to_account='商户A', ensure_accounts=False)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT count(*) FROM transactions WHERE to_account=?', ('商户A',))
        assert c.fetchone()[0] == 1
        conn.close()

    def test_filter_by_from_account(self, temp_db):
        tx_module.add_transaction('支出', 30, '餐饮', '', '微信', '', '', '', '', from_account='微信', to_account='商户B', ensure_accounts=False)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT count(*) FROM transactions WHERE from_account=?', ('微信',))
        assert c.fetchone()[0] == 1
        conn.close()


class TestImportDualAccount:
    """导入双账户与配对测试"""

    def test_preview_import_maps_dual_accounts(self, temp_db):
        import_engine.DB_PATH = temp_db
        csv = '转出账户,转入账户,交易类型,日期,金额,类别\n微信,支付宝,转账,2024-06-15 10:00,1000,转账\n'
        result = import_engine.preview_import(csv.encode('utf-8'), filename='test.csv')
        assert result['preview_rows'][0]['from_account'] == '微信'
        assert result['preview_rows'][0]['to_account'] == '支付宝'

    def test_execute_import_creates_dual_accounts(self, temp_db):
        import_engine.DB_PATH = temp_db
        csv = '转出账户,转入账户,交易类型,日期,金额,类别\n微信,支付宝,转账,2024-06-15 10:00,1000,转账\n'
        mapping = {'转出账户': 'from_account', '转入账户': 'to_account', '交易类型': 'type', '日期': 'date', '金额': 'amount', '类别': 'category'}
        result = import_engine.execute_import(csv.encode('utf-8'), mapping, tags=[], filename='test.csv')
        assert result['imported'] == 1

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT from_account, to_account FROM transactions WHERE batch_id=?', (result['batch_id'],))
        row = c.fetchone()
        conn.close()
        assert row[0] == '微信'
        assert row[1] == '支付宝'

    def test_suishouji_pair_merge(self, temp_db):
        import_engine.DB_PATH = temp_db
        csv = '交易类型,日期,金额,类别,账户,备注\n支出,2024-06-15 10:00,500,借出,微信,借给张三\n收入,2024-06-15 10:00,500,借入,张三,借给张三\n'
        mapping = {'交易类型': 'type', '日期': 'date', '金额': 'amount', '类别': 'category', '账户': 'account', '备注': 'note'}
        result = import_engine.execute_import(csv.encode('utf-8'), mapping, tags=[], filename='suishouji.csv', batch_source='随手记')
        assert result['imported'] == 1

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute('SELECT from_account, to_account, type FROM transactions WHERE batch_id=?', (result['batch_id'],))
        row = c.fetchone()
        conn.close()
        assert row[0] == '微信'
        assert row[1] == '张三'
        assert row[2] == '债权变更'
