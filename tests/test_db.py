#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库初始化与表结构测试"""

import sqlite3
import os

import ledger_modules.db as db_module


class TestDatabaseInit:
    """数据库初始化测试"""

    def test_init_creates_tables(self, temp_db):
        """初始化后应创建 transactions, budgets, budget_templates 三张表"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in c.fetchall()}
        conn.close()
        assert "transactions" in tables
        assert "budgets" in tables
        assert "budget_templates" in tables

    def test_init_creates_db_file(self, temp_db):
        """数据库文件应实际存在"""
        assert os.path.exists(temp_db)

    def test_transactions_table_columns(self, temp_db):
        """transactions 表应有正确的列"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("PRAGMA table_info(transactions)")
        cols = {row[1] for row in c.fetchall()}
        conn.close()
        for col in ["id", "type", "amount", "category", "subcategory", "account",
                     "project", "member", "merchant", "note", "trans_date", "is_deleted"]:
            assert col in cols, f"缺少列: {col}"

    def test_budgets_table_columns(self, temp_db):
        """budgets 表应有正确的列"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("PRAGMA table_info(budgets)")
        cols = {row[1] for row in c.fetchall()}
        conn.close()
        for col in ["id", "category", "year", "month", "amount", "dimension_type", "dimension_value"]:
            assert col in cols, f"缺少列: {col}"

    def test_budget_templates_table_columns(self, temp_db):
        """budget_templates 表应有正确的列"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("PRAGMA table_info(budget_templates)")
        cols = {row[1] for row in c.fetchall()}
        conn.close()
        for col in ["id", "name", "description", "category", "amount",
                     "dimension_type", "dimension_value", "created_at"]:
            assert col in cols, f"缺少列: {col}"

    def test_idempotent_init(self, temp_db):
        """多次初始化不应报错"""
        db_module.init_db()  # 第二次
        db_module.init_db()  # 第三次
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in c.fetchall()]
        conn.close()
        # 核心三张表必须存在
        assert "transactions" in tables
        assert "budgets" in tables
        assert "budget_templates" in tables

    def test_is_deleted_migration(self, temp_db):
        """is_deleted 列应存在（兼容旧表迁移）"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("PRAGMA table_info(transactions)")
        cols = {row[1] for row in c.fetchall()}
        conn.close()
        assert "is_deleted" in cols
