#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 共享 fixtures
自动管理临时数据库，所有测试互不干扰。
"""

import os
import sys
import tempfile
import shutil
import sqlite3
from datetime import datetime

import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 导入模块（在 fixture 中会动态设置 DB_PATH）──
import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module


@pytest.fixture
def temp_db():
    """
    创建临时数据库，确保所有模块使用同一路径。
    测试结束后自动清理临时目录。
    """
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "test.db")

    # 保存原始路径
    orig_paths = {
        "db": db_module.DB_PATH,
        "tx": tx_module.DB_PATH,
        "budget": budget_module.DB_PATH,
    }

    # 设置临时路径
    db_module.DB_PATH = temp_path
    tx_module.DB_PATH = temp_path
    budget_module.DB_PATH = temp_path

    # 初始化表结构
    db_module.init_db()

    yield temp_path  # ← 测试在此执行

    # 清理
    db_module.DB_PATH = orig_paths["db"]
    tx_module.DB_PATH = orig_paths["tx"]
    budget_module.DB_PATH = orig_paths["budget"]
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_db(temp_db):
    """
    在临时数据库中插入示例交易数据。
    依赖 temp_db 自动创建和清理。
    """
    tx_module.add_transaction("expense", 100.0, "食品", "零食", "微信", "项目A", "本人", "拼多多", "零食", "2026-06-15 10:00:00")
    tx_module.add_transaction("expense", 200.0, "交通", "打车", "支付宝", "项目A", "本人", "滴滴", "打车", "2026-06-14 14:30:00")
    tx_module.add_transaction("income", 5000.0, "工资", "", "银行", "", "本人", "", "6月工资", "2026-06-10 09:00:00")
    tx_module.add_transaction("expense", 30.0, "食品", "水果", "微信", "", "fish", "水果店", "水果", "2026-06-12 18:00:00")
    tx_module.add_transaction("expense", 150.0, "餐饮", "午餐", "xxx信用卡", "个人项目", "本人", "食堂", "午餐", "2026-06-13 12:00:00")
    return temp_db


def get_rows(db_path, table="transactions", where="1=1"):
    """便捷工具：查询数据库并返回行列表"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table} WHERE {where}")
    rows = c.fetchall()
    conn.close()
    return rows
