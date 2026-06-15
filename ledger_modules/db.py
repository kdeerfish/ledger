import os
import sqlite3
from datetime import datetime

from .config import get_db_path

# 从配置文件获取数据库路径
DB_PATH = get_db_path()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        subcategory TEXT,
        account TEXT,
        project TEXT,
        member TEXT,
        merchant TEXT,
        note TEXT,
        trans_date TEXT NOT NULL,
        is_deleted INTEGER DEFAULT 0
    )''')

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budgets'")
    if c.fetchone() is None:
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

    # 通用记录模板表
    c.execute('''CREATE TABLE IF NOT EXISTS record_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        template_type TEXT NOT NULL DEFAULT '通用',
        type TEXT,
        amount REAL DEFAULT 0,
        category TEXT,
        subcategory TEXT,
        account TEXT,
        project TEXT,
        member TEXT,
        merchant TEXT,
        note TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used_at TEXT,
        created_at TEXT NOT NULL
    )''')

    c.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in c.fetchall()]
    if 'is_deleted' not in columns:
        c.execute('ALTER TABLE transactions ADD COLUMN is_deleted INTEGER DEFAULT 0')

    # 自动迁移 type 字段从英文到中文
    _migrate_type_to_chinese(c)

    # 迁移 budget_templates 到 record_templates
    _migrate_budget_templates(c)

    conn.commit()
    conn.close()


def _migrate_type_to_chinese(cursor):
    """
    自动将 type 字段从英文迁移到中文
    在 init_db 中调用，每次启动时检查
    """
    # 检查是否有英文类型的记录
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE type IN ('income', 'expense')")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"🔄 检测到 {count} 条英文类型记录，自动迁移到中文...")
        
        # 迁移 income -> 收入
        cursor.execute("UPDATE transactions SET type = '收入' WHERE type = 'income'")
        income_count = cursor.rowcount
        
        # 迁移 expense -> 支出
        cursor.execute("UPDATE transactions SET type = '支出' WHERE type = 'expense'")
        expense_count = cursor.rowcount
        
        print(f"  ✅ 迁移完成: income->收入({income_count}), expense->支出({expense_count})")


def _migrate_budget_templates(cursor):
    """
    将 budget_templates 表的数据迁移到 record_templates 表
    """
    # 检查 record_templates 表是否有数据
    cursor.execute("SELECT COUNT(*) FROM record_templates")
    count = cursor.fetchone()[0]
    
    if count > 0:
        return  # 已经有数据，不需要迁移
    
    # 检查 budget_templates 表是否有数据
    cursor.execute("SELECT COUNT(*) FROM budget_templates")
    budget_count = cursor.fetchone()[0]
    
    if budget_count == 0:
        return  # 没有数据需要迁移
    
    print(f"🔄 迁移 {budget_count} 条预算模板到通用模板...")
    
    # 迁移数据
    cursor.execute('''INSERT INTO record_templates 
        (name, description, template_type, type, amount, category, subcategory, 
         account, project, member, merchant, note, created_at)
        SELECT name, description, '预算', '支出', amount, category, NULL,
               account, project, member, merchant, note, created_at
        FROM budget_templates''')
    
    migrated = cursor.rowcount
    print(f"  ✅ 迁移完成: {migrated} 条模板")
