import os
import sqlite3
from datetime import datetime

from .config import get_db_path

# 从配置文件获取数据库路径
DB_PATH = get_db_path()

# 数据库版本管理
DB_VERSION = 4


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

    # 交易记录表
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        subcategory TEXT,
        account TEXT,
        from_account TEXT,
        to_account TEXT,
        project TEXT,
        member TEXT,
        merchant TEXT,
        note TEXT,
        trans_date TEXT NOT NULL,
        is_deleted INTEGER DEFAULT 0,
        extra_data TEXT,
        batch_id INTEGER
    )''')

    # 账户表
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        account_type TEXT NOT NULL DEFAULT 'self',
        owner TEXT DEFAULT '',
        parent_account TEXT DEFAULT '',
        opening_balance REAL NOT NULL DEFAULT 0,
        color TEXT DEFAULT '#6366f1',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    )''')

    # 账户余额快照表
    c.execute('''CREATE TABLE IF NOT EXISTS account_balances (
        account_name TEXT PRIMARY KEY,
        balance REAL NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    )''')

    # 预算表
    c.execute('''CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        year INTEGER,
        month INTEGER,
        amount REAL,
        dimension_type TEXT DEFAULT 'category',
        dimension_value TEXT,
        UNIQUE(category, year, month, dimension_type, dimension_value)
    )''')

    # 预算模板表
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
        from_account TEXT,
        to_account TEXT,
        project TEXT,
        member TEXT,
        merchant TEXT,
        note TEXT,
        tags TEXT DEFAULT '',
        usage_count INTEGER DEFAULT 0,
        last_used_at TEXT,
        created_at TEXT NOT NULL
    )''')

    # Tags 表
    c.execute('''CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#6366f1',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    )''')

    # 交易-Tag 关联表（多对多）
    c.execute('''CREATE TABLE IF NOT EXISTS transaction_tags (
        transaction_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (transaction_id, tag_id),
        FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    )''')

    # 导入批次追踪表
    c.execute('''CREATE TABLE IF NOT EXISTS import_batches (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        source      TEXT NOT NULL,
        filename    TEXT,
        row_count   INTEGER DEFAULT 0,
        mapping     TEXT,
        tags        TEXT,
        created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    )''')

    # AI Agent 多套配置
    c.execute('''CREATE TABLE IF NOT EXISTS agent_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        base_url TEXT,
        api_key TEXT,
        system_prompt TEXT,
        is_default INTEGER DEFAULT 0,
        is_enabled INTEGER DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    )''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_agent_configs_user ON agent_configs(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_agent_configs_default ON agent_configs(user_id, is_default)")

    # 索引
    c.execute("PRAGMA index_list(transactions)")
    indexes = {row[2] for row in c.fetchall()}
    if 'idx_trans_date' not in indexes:
        c.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(trans_date)")
    if 'idx_trans_category' not in indexes:
        c.execute("CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category)")
    if 'idx_trans_type' not in indexes:
        c.execute("CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(type)")
    if 'idx_trans_merchant' not in indexes:
        c.execute("CREATE INDEX IF NOT EXISTS idx_trans_merchant ON transactions(merchant)")
    if 'idx_trans_account' not in indexes:
        c.execute("CREATE INDEX IF NOT EXISTS idx_trans_account ON transactions(account)")
    
    # 仅在列存在时创建索引
    tx_cols = {row[1] for row in c.execute("PRAGMA table_info(transactions)").fetchall()}
    if 'from_account' in tx_cols and 'idx_trans_from_account' not in indexes:
        c.execute("CREATE INDEX IF NOT EXISTS idx_trans_from_account ON transactions(from_account)")
    if 'to_account' in tx_cols and 'idx_trans_to_account' not in indexes:
        c.execute("CREATE INDEX IF NOT EXISTS idx_trans_to_account ON transactions(to_account)")
    
    # accounts 表索引
    c.execute("PRAGMA index_list(accounts)")
    account_indexes = {row[2] for row in c.fetchall()}
    if 'idx_accounts_type' not in account_indexes:
        c.execute("CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type)")

    # 数据库版本迁移
    current_version = _get_db_version(c)
    if current_version < 4:
        c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('db_version', '4')")

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
                 WHERE tt.transaction_id = ? AND t.is_deleted = 0
                 ORDER BY t.trans_date DESC LIMIT ? OFFSET ?''', (tag_id, limit, offset))
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'date': r[1], 'type': r[2], 'amount': r[3],
             'category': r[4], 'account': r[5], 'note': r[6]} for r in rows]


# ─── 账户管理 ──────────────────────────────────────────────

def get_all_accounts():
    """获取所有账户"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, account_type, owner, parent_account, opening_balance, color, created_at FROM accounts ORDER BY account_type, name")
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'account_type': r[2], 'owner': r[3], 'parent_account': r[4],
             'opening_balance': r[5], 'color': r[6], 'created_at': r[7]} for r in rows]


def create_account(name, account_type='self', owner='', parent_account='', opening_balance=0, color='#6366f1'):
    """创建账户"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO accounts (name, account_type, owner, parent_account, opening_balance, color) VALUES (?, ?, ?, ?, ?, ?)",
                  (name.strip(), account_type, owner.strip(), parent_account.strip(), opening_balance, color))
        account_id = c.lastrowid
        conn.commit()
        return account_id
    except sqlite3.IntegrityError:
        c.execute("SELECT id FROM accounts WHERE name = ?", (name.strip(),))
        row = c.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def update_account(account_id, **kwargs):
    """更新账户信息"""
    allowed = {'name', 'account_type', 'owner', 'parent_account', 'opening_balance', 'color'}
    fields = []
    values = []
    for k, v in kwargs.items():
        if k in allowed:
            fields.append(f"{k} = ?")
            values.append(v)
    if not fields:
        return False
    values.append(account_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE accounts SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def delete_account(account_id):
    """删除账户"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def get_account_by_name(name):
    """根据名称获取账户"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, account_type, owner, parent_account, opening_balance, color, created_at FROM accounts WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'name': row[1], 'account_type': row[2], 'owner': row[3], 'parent_account': row[4],
                'opening_balance': row[5], 'color': row[6], 'created_at': row[7]}
    return None


def ensure_account(name, account_type='self', owner='', parent_account='', opening_balance=0, color='#6366f1'):
    """确保账户存在，不存在则创建"""
    account = get_account_by_name(name)
    if account:
        return account['id']
    return create_account(name, account_type, owner, parent_account, opening_balance, color)


# ─── 账户余额计算 ──────────────────────────────────────────

def get_account_balance(account_name):
    """计算账户余额：到账 - 出账"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN to_account = ? THEN amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN from_account = ? THEN amount ELSE 0 END), 0)
        FROM transactions
        WHERE is_deleted = 0
          AND (to_account = ? OR from_account = ?)
    """, (account_name, account_name, account_name, account_name))
    balance = c.fetchone()[0]
    conn.close()
    return balance


def get_account_balances_with_type():
    """获取所有账户余额，包含账户类型信息"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT 
            a.name,
            a.account_type,
            a.owner,
            a.parent_account,
            a.opening_balance,
            COALESCE(SUM(CASE WHEN t.to_account = a.name THEN t.amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN t.from_account = a.name THEN t.amount ELSE 0 END), 0) as transaction_balance
        FROM accounts a
        LEFT JOIN transactions t ON t.is_deleted = 0 AND (t.to_account = a.name OR t.from_account = a.name)
        GROUP BY a.name, a.account_type, a.owner, a.parent_account, a.opening_balance
        ORDER BY a.account_type, a.name
    """)
    rows = c.fetchall()
    conn.close()
    result = []
    for r in rows:
        name, account_type, owner, parent_account, opening_balance, transaction_balance = r
        balance = (opening_balance or 0) + (transaction_balance or 0)
        result.append({
            'name': name,
            'account_type': account_type,
            'owner': owner,
            'parent_account': parent_account,
            'opening_balance': opening_balance or 0,
            'transaction_balance': transaction_balance or 0,
            'balance': balance,
        })
    return result


def get_net_worth():
    """计算净资产：self + claims - liability"""
    balances = get_account_balances_with_type()
    net = 0
    for b in balances:
        if b['account_type'] in ('self', 'claims'):
            net += b['balance']
        elif b['account_type'] == 'liability':
            net -= b['balance']
    return net


def recalc_account_balances(conn, account_names):
    """重新计算指定账户的余额并写入 account_balances 表"""
    c = conn.cursor()
    for name in account_names:
        c.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN to_account = ? THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN from_account = ? THEN amount ELSE 0 END), 0)
            FROM transactions
            WHERE is_deleted = 0
              AND (to_account = ? OR from_account = ?)
        """, (name, name, name, name))
        balance = c.fetchone()[0] or 0
        c.execute("""
            INSERT INTO account_balances (account_name, balance, updated_at)
            VALUES (?, ?, datetime('now', 'localtime'))
            ON CONFLICT(account_name) DO UPDATE SET balance = excluded.balance, updated_at = excluded.updated_at
        """, (name, balance))
