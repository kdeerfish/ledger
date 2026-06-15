#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import csv
import sys
import os
from datetime import datetime

# ================== 配置区 ==================
# 数据库路径（可通过环境变量 LEDGER_DB_PATH 覆盖）
DB_PATH = os.environ.get('LEDGER_DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.db"))
# ===========================================

def init_db():
    """创建所有必要的表（如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. 交易流水表
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,              -- 'expense' 或 'income'
        amount REAL NOT NULL,
        category TEXT,
        subcategory TEXT,
        account TEXT,
        project TEXT,
        member TEXT,
        merchant TEXT,
        note TEXT,
        trans_date TEXT NOT NULL,         -- 格式 YYYY-MM-DD HH:MM:SS
        is_deleted INTEGER DEFAULT 0
    )''')

    # 2. 预算表
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budgets'")
    budgets_exists = c.fetchone() is not None
    if not budgets_exists:
        c.execute('''CREATE TABLE budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            year INTEGER,
            month INTEGER,
            amount REAL,
            dimension_type TEXT DEFAULT 'category',
            dimension_value TEXT,
            UNIQUE(category, year, month, dimension_type, dimension_value)
        )''')
    else:
        c.execute("PRAGMA table_info(budgets)")
        columns = [row[1] for row in c.fetchall()]
        if 'dimension_type' not in columns or 'dimension_value' not in columns:
            c.execute('ALTER TABLE budgets RENAME TO budgets_old')
            c.execute('''CREATE TABLE budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                year INTEGER,
                month INTEGER,
                amount REAL,
                dimension_type TEXT DEFAULT 'category',
                dimension_value TEXT,
                UNIQUE(category, year, month, dimension_type, dimension_value)
            )''')
            c.execute("""INSERT INTO budgets (id, category, year, month, amount, dimension_type, dimension_value)
                         SELECT id, category, year, month, amount, 'category', NULL FROM budgets_old""")
            c.execute('DROP TABLE budgets_old')

    c.execute('''CREATE TABLE IF NOT EXISTS budget_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        amount REAL DEFAULT 0,
        dimension_type TEXT DEFAULT 'category',
        dimension_value TEXT,
        account TEXT,
        project TEXT,
        member TEXT,
        merchant TEXT,
        note TEXT,
        year INTEGER,
        month INTEGER,
        created_at TEXT NOT NULL
    )''')

    # 迁移：如果 transactions 表缺少 is_deleted 列，添加它
    c.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in c.fetchall()]
    if 'is_deleted' not in columns:
        c.execute('ALTER TABLE transactions ADD COLUMN is_deleted INTEGER DEFAULT 0')
        print("已为 transactions 表添加 is_deleted 列")

    conn.commit()
    conn.close()
    print(f"数据库表结构检查/创建完成，数据库位置: {DB_PATH}")

def import_csv(csv_file):
    """导入随手记导出的 CSV 文件"""
    if not os.path.exists(csv_file):
        print(f"文件不存在: {csv_file}")
        return False

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    total_rows = 0
    imported = 0
    skipped = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # 检查必要的列是否存在
        required_cols = ['交易类型', '日期', '金额', '账户']
        missing = [col for col in required_cols if col not in reader.fieldnames]
        if missing:
            print(f"CSV 缺少必要列: {missing}")
            return False

        for row in reader:
            total_rows += 1

            # 1. 解析交易类型
            type_raw = row.get('交易类型', '').strip()
            if type_raw == '支出':
                tx_type = 'expense'
            elif type_raw == '收入':
                tx_type = 'income'
            else:
                # 跳过转账、不计收支等类型
                skipped += 1
                continue

            # 2. 解析金额
            try:
                amount_str = row.get('金额', '0').strip()
                if not amount_str:
                    skipped += 1
                    continue
                amount = float(amount_str)
            except (ValueError, TypeError):
                amount = 0.0
            if amount == 0:
                skipped += 1
                continue

            # 3. 解析日期时间 (随手记格式: 2026/6/13 1:34 或 2026/6/13)
            raw_date = row.get('日期', '').strip()
            if not raw_date:
                skipped += 1
                continue
            try:
                # 尝试带时间
                dt = datetime.strptime(raw_date, '%Y/%m/%d %H:%M')
                trans_date = dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    # 仅日期
                    dt = datetime.strptime(raw_date, '%Y/%m/%d')
                    trans_date = dt.strftime('%Y-%m-%d 00:00:00')
                except ValueError:
                    print(f"日期格式错误: {raw_date}，跳过此行")
                    skipped += 1
                    continue

            # 4. 其他字段
            category = row.get('类别', '').strip()
            subcategory = row.get('子类别', '').strip()
            account = row.get('账户', '').strip()
            project = row.get('项目', '').strip()
            member = row.get('成员', '').strip()
            merchant = row.get('商家', '').strip()
            note = row.get('备注', '').strip()

            # 5. 插入交易记录
            c.execute('''INSERT INTO transactions
                (type, amount, category, subcategory, account, project, member, merchant, note, trans_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (tx_type, amount, category, subcategory, account, project, member, merchant, note, trans_date))

            imported += 1

    conn.commit()
    conn.close()

    print(f"\n导入统计:")
    print(f"   总行数: {total_rows}")
    print(f"   成功导入: {imported}")
    print(f"   跳过 (非收支/金额为空/日期错误): {skipped}")
    print(f"导入完成，数据库位置: {DB_PATH}")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python import_ledger.py <CSV文件路径>")
        print("示例: python import_ledger.py mymoney_data.csv")
        sys.exit(1)

    csv_file = sys.argv[1]
    # 初始化数据库
    init_db()
    # 导入数据
    import_csv(csv_file)

if __name__ == "__main__":
    main()