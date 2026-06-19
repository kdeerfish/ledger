import os
import sqlite3
from datetime import datetime

from .config import get_db_path

# 从配置文件获取数据库路径
DB_PATH = get_db_path()

# 数据库版本管理
DB_VERSION = 2


def _get_db_version(c):
    """获取数据库版本号"""
    try:
        c.execute("SELECT value FROM meta WHERE key='db_version'")
        row = c.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.OperationalError as e:
        import sys
        db_dir = os.path.dirname(DB_PATH) if DB_PATH else '(unknown)'
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"  数据库连接失败: {e}", file=sys.stderr)
        print(f"  数据库路径: {DB_PATH}", file=sys.stderr)
        print(f"  数据库目录: {db_dir}", file=sys.stderr)
        if db_dir and not os.access(db_dir, os.W_OK):
            print(f"\n  原因: 目录 {db_dir} 没有写入权限", file=sys.stderr)
            print(f"  当前用户: uid={os.getuid()}, gid={os.getgid()}", file=sys.stderr)
            print(f"\n  解决方法:", file=sys.stderr)
            print(f"    1. 在宿主机上执行: chmod 777 {db_dir}", file=sys.stderr)
            print(f"    2. 或在 docker-compose.yml 中添加: user: \"0:0\"", file=sys.stderr)
            print(f"    3. 或重新构建镜像确保容器用户 UID 与宿主机目录所有者一致", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        raise
    c = conn.cursor()

    # 元数据表
    c.execute('''CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )''')

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

    # ── Tags 表 ──
    c.execute('''CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#6366f1',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    )''')

    # ── 交易-Tag 关联表（多对多） ──
    c.execute('''CREATE TABLE IF NOT EXISTS transaction_tags (
        transaction_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (transaction_id, tag_id),
        FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    )''')

    # ── record_templates 扩展 tags 字段 ──
    c.execute("PRAGMA table_info(record_templates)")
    tmpl_columns = [row[1] for row in c.fetchall()]
    if 'tags' not in tmpl_columns:
        try:
            c.execute('ALTER TABLE record_templates ADD COLUMN tags TEXT DEFAULT ""')
        except Exception:
            pass

    # ── 迁移：确保 is_deleted 列存在 ──
    c.execute("PRAGMA table_info(transactions)")
    tx_cols = [row[1] for row in c.fetchall()]
    if 'is_deleted' not in tx_cols:
        try:
            c.execute('ALTER TABLE transactions ADD COLUMN is_deleted INTEGER DEFAULT 0')
        except Exception:
            pass

    # ── 数据库迁移 ──
    current_version = _get_db_version(c)
    if current_version < 2:
        # 迁移到 v2: 确保 transactions 表有必要索引
        c.execute("PRAGMA index_list(transactions)")
        indexes = [row[2] for row in c.fetchall()]
        if 'idx_trans_date' not in indexes:
            c.execute("CREATE INDEX idx_trans_date ON transactions(trans_date)")
        if 'idx_trans_category' not in indexes:
            c.execute("CREATE INDEX idx_trans_category ON transactions(category)")
        if 'idx_trans_type' not in indexes:
            c.execute("CREATE INDEX idx_trans_type ON transactions(type)")
        c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('db_version', '2')")

    conn.commit()
    conn.close()


# ─── Tag 辅助函数 ──────────────────────────────────────────

def get_all_tags():
    """获取所有标签"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, color, created_at FROM tags ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'color': r[2], 'created_at': r[3]} for r in rows]


def create_tag(name, color='#6366f1'):
    """创建新标签，返回 tag id"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO tags (name, color) VALUES (?, ?)", (name.strip(), color))
        tag_id = c.lastrowid
        conn.commit()
        return tag_id
    except sqlite3.IntegrityError:
        # 标签已存在，返回已有 id
        c.execute("SELECT id FROM tags WHERE name = ?", (name.strip(),))
        row = c.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def delete_tag(tag_id):
    """删除标签"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM transaction_tags WHERE tag_id = ?", (tag_id,))
    c.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    conn.commit()
    conn.close()


def set_transaction_tags(transaction_id, tag_ids):
    """设置交易的标签（先清空再设置）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM transaction_tags WHERE transaction_id = ?", (transaction_id,))
    for tag_id in tag_ids:
        c.execute("INSERT OR IGNORE INTO transaction_tags (transaction_id, tag_id) VALUES (?, ?)",
                  (transaction_id, tag_id))
    conn.commit()
    conn.close()


def get_transaction_tags(transaction_id):
    """获取交易的标签列表"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT t.id, t.name, t.color
                 FROM tags t
                 JOIN transaction_tags tt ON t.id = tt.tag_id
                 WHERE tt.transaction_id = ?''', (transaction_id,))
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'color': r[2]} for r in rows]


def get_transactions_by_tag(tag_id, limit=50, offset=0):
    """获取某标签下的所有交易"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT t.id, t.trans_date, t.type, t.amount, t.category, t.account, t.note
                 FROM transactions t
                 JOIN transaction_tags tt ON t.id = tt.transaction_id
                 WHERE tt.tag_id = ? AND t.is_deleted = 0
                 ORDER BY t.trans_date DESC LIMIT ? OFFSET ?''', (tag_id, limit, offset))
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'date': r[1], 'type': r[2], 'amount': r[3],
             'category': r[4], 'account': r[5], 'note': r[6]} for r in rows]
