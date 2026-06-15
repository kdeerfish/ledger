import os
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get('LEDGER_DB_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ledger.db'))


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

    c.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in c.fetchall()]
    if 'is_deleted' not in columns:
        c.execute('ALTER TABLE transactions ADD COLUMN is_deleted INTEGER DEFAULT 0')

    conn.commit()
    conn.close()
