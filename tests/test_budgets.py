#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预算与模板功能测试"""

import sqlite3

import ledger_modules.budgets as budget_module
import ledger_modules.transactions as tx_module


class TestBudgetSetCheck:
    """预算设置与检查测试"""

    def test_set_budget(self, temp_db):
        budget_module.set_budget("食品", 1000.0, 2026, 6)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT amount FROM budgets WHERE category='食品' AND year=2026 AND month=6")
        row = c.fetchone()
        conn.close()
        assert row is not None
        assert row[0] == 1000.0

    def test_budget_with_spending(self, temp_db):
        budget_module.set_budget("食品", 1000.0, 2026, 6)
        tx_module.add_transaction("expense", 300.0, "食品", "", "", "", "", "", "", "2026-06-15 10:00:00")

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT amount FROM budgets WHERE category='食品'")
        budget_amt = c.fetchone()[0]
        c.execute("""SELECT SUM(amount) FROM transactions
                     WHERE type='expense' AND category='食品'
                     AND strftime('%Y', trans_date)='2026'
                     AND strftime('%m', trans_date)='06' AND is_deleted=0""")
        spent = c.fetchone()[0]
        conn.close()

        assert budget_amt == 1000.0
        assert spent == 300.0

    def test_budget_no_spending(self, temp_db):
        """有预算但无支出时已用应为0"""
        budget_module.set_budget("交通", 500.0, 2026, 6)
        spent = budget_module._get_budget_spent("交通", 2026, 6)
        assert spent == 0.0


class TestMultiDimensionBudget:
    """多维度预算测试"""

    def test_budget_by_account(self, temp_db):
        budget_module.set_budget("午餐", 500.0, 2026, 6, dimension_type="account", dimension_value="xxx信用卡")
        tx_module.add_transaction("expense", 120.0, "餐饮", "", "xxx信用卡", "个人项目", "本人", "", "午餐", "2026-06-10 12:00:00")

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT amount, dimension_type, dimension_value FROM budgets WHERE category='午餐'")
        row = c.fetchone()
        c.execute("""SELECT SUM(amount) FROM transactions
                     WHERE type='expense' AND account='xxx信用卡'
                     AND strftime('%Y', trans_date)='2026'
                     AND strftime('%m', trans_date)='06' AND is_deleted=0""")
        spent = c.fetchone()[0]
        conn.close()

        assert row[0] == 500.0
        assert row[1] == "account"
        assert row[2] == "xxx信用卡"
        assert spent == 120.0


class TestBudgetTemplates:
    """预算模板 CRUD + 应用测试"""

    def test_create_template(self, temp_db):
        template_id = budget_module.create_budget_template(
            name="吃饭模板", description="日常吃饭", category="餐饮",
            dimension_type="account", dimension_value="xxx信用卡",
            amount=400.0, account="xxx信用卡", member="本人", year=2026, month=6,
        )
        assert template_id is not None
        assert template_id > 0

    def test_list_templates(self, temp_db):
        budget_module.create_budget_template("模板A")
        budget_module.create_budget_template("模板B")
        templates = budget_module.list_budget_templates()
        names = {t["name"] for t in templates}
        assert "模板A" in names
        assert "模板B" in names

    def test_update_template(self, temp_db):
        tid = budget_module.create_budget_template("初始模板", amount=100.0)
        result = budget_module.update_budget_template(tid, amount=500.0, description="更新描述")
        assert result

        templates = budget_module.list_budget_templates()
        t = next(item for item in templates if item["id"] == tid)
        assert t["amount"] == 500.0
        assert t["description"] == "更新描述"

    def test_delete_template(self, temp_db):
        tid = budget_module.create_budget_template("待删除")
        assert budget_module.delete_budget_template(tid)
        templates = budget_module.list_budget_templates()
        assert not any(t["id"] == tid for t in templates)

    def test_apply_template_creates_budget(self, temp_db):
        tid = budget_module.create_budget_template(
            name="吃饭模板", description="日常吃饭", category="餐饮",
            dimension_type="account", dimension_value="xxx信用卡",
            amount=400.0, account="xxx信用卡", member="本人", year=2026, month=6,
        )
        result = budget_module.apply_budget_template(tid, 2026, 6)
        assert result is not None
        assert result["category"] is not None

    def test_apply_invalid_template(self, temp_db):
        result = budget_module.apply_budget_template(9999, 2026, 6)
        assert result is None

    def test_template_full_cycle(self, temp_db):
        """增→查→改→应用→删 全流程"""
        tid = budget_module.create_budget_template("全流程", amount=300.0, category="餐饮")

        # 查
        templates = budget_module.list_budget_templates()
        assert any(t["id"] == tid for t in templates)

        # 改
        budget_module.update_budget_template(tid, amount=500.0, description="已修改")

        # 应用
        budget_module.apply_budget_template(tid, 2026, 6)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM budgets WHERE year=2026 AND month=6")
        assert c.fetchone()[0] >= 1
        conn.close()

        # 删
        budget_module.delete_budget_template(tid)
        assert not any(t["id"] == tid for t in budget_module.list_budget_templates())

    def test_suggest_templates(self, temp_db):
        """基于历史交易自动生成模板建议"""
        tx_module.add_transaction("expense", 20.0, "餐饮", "", "xxx信用卡", "个人项目", "本人", "", "午饭", "2026-06-10 12:00:00")
        tx_module.add_transaction("expense", 22.0, "餐饮", "", "xxx信用卡", "个人项目", "本人", "", "晚饭", "2026-06-11 19:00:00")

        suggestions = budget_module.suggest_budget_templates(limit=3)
        assert len(suggestions) >= 1
        assert suggestions[0]["category"] == "餐饮"
