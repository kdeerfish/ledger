#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""集成测试 - 端到端工作流"""

import os
import csv
import tempfile
import sqlite3

import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module


class TestEndToEnd:
    """端到端工作流测试"""

    def test_full_workflow(self, temp_db):
        """完整记账流程：添加→查询→修改→删除→恢复→汇总"""
        # 1. 添加收支
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "零食", "2026-06-15")
        tx_module.add_transaction("收入", 5000.0, "工资", "", "银行", "", "本人", "", "工资", "2026-06-10")

        # 2. 查询
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions WHERE is_deleted=0")
        assert c.fetchone()[0] == 2
        conn.close()

        # 3. 修改
        tx_module.update_transaction(1, "amount", "150.0")
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT amount FROM transactions WHERE id=1")
        assert c.fetchone()[0] == 150.0
        conn.close()

        # 4. 软删除
        tx_module.soft_delete_transaction(1)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT is_deleted FROM transactions WHERE id=1")
        assert c.fetchone()[0] == 1
        conn.close()

        # 5. 恢复
        tx_module.restore_transaction(1)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT is_deleted FROM transactions WHERE id=1")
        assert c.fetchone()[0] == 0
        conn.close()

        # 6. 汇总
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT type, SUM(amount) FROM transactions WHERE is_deleted=0 GROUP BY type")
        data = {r[0]: r[1] for r in c.fetchall()}
        conn.close()
        assert data.get("支出") == 150.0
        assert data.get("收入") == 5000.0

    def test_budget_with_transactions(self, temp_db):
        """设置预算 → 添加支出 → 检查预算使用情况"""
        budget_module.set_budget("食品", 1000.0, 2026, 6)
        tx_module.add_transaction("支出", 300.0, "食品", "", "", "", "", "", "", "2026-06-15")
        tx_module.add_transaction("支出", 200.0, "食品", "", "", "", "", "", "", "2026-06-16")

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT amount FROM budgets WHERE category='食品'")
        budget_amt = c.fetchone()[0]
        c.execute("""SELECT SUM(amount) FROM transactions
                     WHERE category='食品' AND is_deleted=0""")
        spent = c.fetchone()[0]
        conn.close()

        assert budget_amt == 1000.0
        assert spent == 500.0  # 300 + 200

    def test_multi_dimension_budget_workflow(self, temp_db):
        """多维度预算：按账户 + 成员组合"""
        # 预算 category 需与交易 category 匹配
        budget_module.set_budget("餐饮", 2000.0, 2026, 6, dimension_type="account", dimension_value="家庭卡")
        budget_module.set_budget("餐饮", 1000.0, 2026, 6, dimension_type="member", dimension_value="本人")

        tx_module.add_transaction("支出", 50.0, "餐饮", "", "家庭卡", "", "本人", "", "买菜", "2026-06-10")
        tx_module.add_transaction("支出", 30.0, "餐饮", "", "家庭卡", "", "fish", "", "买菜", "2026-06-11")

        # 按账户维度检查：家庭卡支出共80
        spent_account = budget_module._get_budget_spent("餐饮", 2026, 6, "account", "家庭卡")
        assert spent_account == 80.0


class TestImportCSV:
    """CSV 导入测试"""

    def test_import_valid_csv(self, temp_db):
        csv_path = os.path.join(tempfile.mkdtemp(), "test.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["交易类型", "日期", "金额", "类别", "子类别", "账户", "项目", "成员", "商家", "备注"])
            writer.writerow(["支出", "2026/06/15 12:30", "25.5", "食品酒水", "零食", "微信零钱", "", "本人", "便利店", "零食"])
            writer.writerow(["收入", "2026/06/10", "5000", "职业收入", "", "招商银行", "", "本人", "", "工资"])

        result = tx_module.import_csv(csv_path)
        assert result

        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions")
        assert c.fetchone()[0] == 2
        conn.close()

    def test_import_skips_non_expense_income(self, temp_db):
        """导入应跳过未识别类型，但保留转账类型"""
        csv_path = os.path.join(tempfile.mkdtemp(), "skip.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["交易类型", "日期", "金额", "类别", "备注"])
            writer.writerow(["支出", "2026/06/15", "100", "食品", ""])
            writer.writerow(["转账", "2026/06/15", "200", "", ""])
            writer.writerow(["不计收支", "2026/06/15", "300", "", ""])

        tx_module.import_csv(csv_path)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions")
        assert c.fetchone()[0] == 2
        conn.close()

    def test_import_missing_file(self, temp_db):
        result = tx_module.import_csv("/nonexistent/file.csv")
        assert not result
