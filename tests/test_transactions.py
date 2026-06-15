#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交易记录 CRUD、搜索、筛选、导出、统计测试"""

import os
import csv
import json
import tempfile
import sqlite3
from datetime import datetime

import pytest

import ledger_modules.transactions as tx_module


class TestAddTransaction:
    """添加交易测试"""

    # SELECT * 的列顺序：
    # 0:id 1:type 2:amount 3:category 4:subcategory
    # 5:account 6:project 7:member 8:merchant 9:note 10:trans_date 11:is_deleted

    def test_add_expense(self, temp_db):
        tx_module.add_transaction("expense", 100.0, "食品", "零食", "微信", "项目", "本人", "商家", "备注", "2026-06-15 10:00:00")
        rows = self._fetch(temp_db)
        assert len(rows) == 1
        assert rows[0][1] == "expense"   # type
        assert rows[0][2] == 100.0       # amount
        assert rows[0][3] == "食品"       # category
        assert rows[0][5] == "微信"       # account
        assert rows[0][7] == "本人"       # member
        assert rows[0][8] == "商家"       # merchant
        assert rows[0][9] == "备注"       # note

    def test_add_income(self, temp_db):
        tx_module.add_transaction("income", 5000.0, "工资", "", "银行", "", "本人", "", "6月工资", "2026-06-10")
        rows = self._fetch(temp_db)
        assert rows[0][1] == "income"
        assert rows[0][2] == 5000.0

    def test_default_date(self, temp_db):
        """不传日期应自动使用当前时间"""
        tx_module.add_transaction("expense", 50.0, "测试", "", "", "", "", "", "", None)
        rows = self._fetch(temp_db)
        assert datetime.now().strftime("%Y-%m-%d") in rows[0][10]  # trans_date

    def test_auto_fields(self, temp_db):
        """账户和成员字段应正确保留"""
        tx_module.add_transaction("expense", 10.0, "测试", "", "账户A", "", "张三", "", "", None)
        rows = self._fetch(temp_db)
        assert rows[0][5] == "账户A"     # account
        assert rows[0][7] == "张三"       # member

    @staticmethod
    def _fetch(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM transactions")
        rows = c.fetchall()
        conn.close()
        return rows


class TestListTransactions:
    """列出交易测试"""

    def test_list_returns_all(self, sample_db):
        """列出交易应返回所有非删除记录"""
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions WHERE is_deleted=0")
        count = c.fetchone()[0]
        conn.close()
        assert count == 5


class TestSummary:
    """汇总统计测试"""

    def test_basic_summary(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("SELECT type, SUM(amount) FROM transactions WHERE is_deleted=0 GROUP BY type")
        data = {r[0]: r[1] for r in c.fetchall()}
        conn.close()
        assert data.get("expense") == pytest.approx(480.0, rel=1e-9)  # 100+200+30+150
        assert data.get("income") == 5000.0

    def test_summary_filter_year_month(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("""SELECT SUM(amount) FROM transactions
                     WHERE type='expense' AND strftime('%Y', trans_date)='2026'
                     AND strftime('%m', trans_date)='06' AND is_deleted=0""")
        row = c.fetchone()
        conn.close()
        assert row[0] == pytest.approx(480.0, rel=1e-9)


class TestUpdateTransaction:
    """更新交易测试"""

    def test_update_amount(self, temp_db):
        tx_module.add_transaction("expense", 100.0, "食品", "", "", "", "", "", "", None)
        tx_module.update_transaction(1, "amount", "200.0")
        tx_module.update_transaction(1, "category", "交通")
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT amount, category FROM transactions WHERE id=1")
        row = c.fetchone()
        conn.close()
        assert row[0] == 200.0
        assert row[1] == "交通"


class TestDeleteTransaction:
    """删除/恢复交易测试"""

    def test_soft_delete(self, temp_db):
        tx_module.add_transaction("expense", 100.0, "食品", "", "", "", "", "", "", None)
        tx_module.soft_delete_transaction(1)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT is_deleted FROM transactions WHERE id=1")
        assert c.fetchone()[0] == 1
        conn.close()

    def test_restore(self, temp_db):
        tx_module.add_transaction("expense", 100.0, "食品", "", "", "", "", "", "", None)
        tx_module.soft_delete_transaction(1)
        tx_module.restore_transaction(1)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT is_deleted FROM transactions WHERE id=1")
        assert c.fetchone()[0] == 0
        conn.close()

    def test_hard_delete(self, temp_db):
        tx_module.add_transaction("expense", 100.0, "食品", "", "", "", "", "", "", None)
        tx_module.hard_delete_transaction(1, confirm=True)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions WHERE id=1")
        assert c.fetchone()[0] == 0
        conn.close()

    def test_hard_delete_requires_confirm(self, temp_db):
        tx_module.add_transaction("expense", 100.0, "食品", "", "", "", "", "", "", None)
        tx_module.hard_delete_transaction(1)  # no confirm
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions WHERE id=1")
        assert c.fetchone()[0] == 1  # should still exist
        conn.close()


class TestSearch:
    """搜索测试"""

    def test_search_by_note(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("""SELECT COUNT(*) FROM transactions
                     WHERE is_deleted=0 AND (note LIKE '%零食%' OR merchant LIKE '%拼多多%')""")
        assert c.fetchone()[0] >= 1
        conn.close()


class TestFilter:
    """筛选测试"""

    def test_filter_by_category(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions WHERE category='食品' AND is_deleted=0")
        assert c.fetchone()[0] == 2
        conn.close()

    def test_filter_by_account(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions WHERE account='微信' AND is_deleted=0")
        assert c.fetchone()[0] == 2
        conn.close()


class TestExport:
    """导出测试"""

    def test_export_csv(self, temp_db):
        tx_module.add_transaction("expense", 100.0, "食品", "", "", "", "", "", "备注", None)
        output = os.path.join(tempfile.mkdtemp(), "export.csv")
        result = tx_module.export_transactions(output, "csv")
        assert result
        assert os.path.exists(output)
        with open(output, "r", encoding="utf-8") as f:
            content = f.read()
            assert "食品" in content
            assert "100.0" in content

    def test_export_json(self, temp_db):
        tx_module.add_transaction("expense", 100.0, "食品", "", "", "", "", "", "备注", None)
        output = os.path.join(tempfile.mkdtemp(), "export.json")
        result = tx_module.export_transactions(output, "json")
        assert result
        assert os.path.exists(output)
        with open(output, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["category"] == "食品"

    def test_export_empty_db(self, temp_db):
        output = os.path.join(tempfile.mkdtemp(), "empty.csv")
        result = tx_module.export_transactions(output, "csv")
        assert not result


class TestStatistics:
    """统计测试"""

    def test_statistics_by_category(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("""SELECT category, type, SUM(amount), COUNT(*)
                     FROM transactions WHERE is_deleted=0
                     GROUP BY category, type ORDER BY SUM(amount) DESC""")
        rows = c.fetchall()
        conn.close()
        assert len(rows) >= 1

    def test_statistics_monthly(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("""SELECT strftime('%Y-%m', trans_date), type, SUM(amount), COUNT(*)
                     FROM transactions WHERE is_deleted=0
                     GROUP BY 1, 2 ORDER BY 1 DESC""")
        rows = c.fetchall()
        conn.close()
        assert rows


class TestListMeta:
    """元数据查询测试"""

    def test_list_accounts(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("SELECT DISTINCT account FROM transactions WHERE is_deleted=0 AND account != ''")
        accounts = {r[0] for r in c.fetchall()}
        conn.close()
        assert "微信" in accounts
        assert "支付宝" in accounts
        assert "银行" in accounts

    def test_list_categories(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("SELECT DISTINCT category FROM transactions WHERE is_deleted=0")
        cats = {r[0] for r in c.fetchall()}
        conn.close()
        assert "食品" in cats
        assert "交通" in cats
        assert "工资" in cats

    def test_list_members(self, sample_db):
        conn = sqlite3.connect(sample_db)
        c = conn.cursor()
        c.execute("SELECT DISTINCT member FROM transactions WHERE is_deleted=0 AND member != ''")
        members = {r[0] for r in c.fetchall()}
        conn.close()
        assert "本人" in members



