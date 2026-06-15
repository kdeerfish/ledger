#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import csv
import sys
import argparse
import os
from datetime import datetime

# ========== 配置 ==========
# 数据库路径（可通过环境变量 LEDGER_DB_PATH 覆盖）
DB_PATH = os.environ.get('LEDGER_DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.db"))
# =========================

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
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS members (name TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (name TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        year INTEGER,
        month INTEGER,
        amount REAL,
        UNIQUE(category, year, month)
    )''')
    # 迁移：如果 transactions 表缺少 is_deleted 列，添加它
    c.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in c.fetchall()]
    if 'is_deleted' not in columns:
        c.execute('ALTER TABLE transactions ADD COLUMN is_deleted INTEGER DEFAULT 0')
    conn.commit()
    conn.close()

def add_transaction(type_, amount, category, subcategory, account, project, member, merchant, note, trans_date=None):
    if trans_date is None:
        trans_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO transactions
        (type, amount, category, subcategory, account, project, member, merchant, note, trans_date, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''',
        (type_, amount, category, subcategory, account, project, member, merchant, note, trans_date))
    new_id = c.lastrowid
    # 自动记录账户、成员、项目
    if account:
        c.execute('INSERT OR IGNORE INTO accounts (name) VALUES (?)', (account,))
    if member:
        c.execute('INSERT OR IGNORE INTO members (name) VALUES (?)', (member,))
    if project:
        c.execute('INSERT OR IGNORE INTO projects (name) VALUES (?)', (project,))
    conn.commit()
    conn.close()
    print(f"已添加记录 ID={new_id}: {type_} {amount} 元 | {category} | {account}")

def list_transactions(limit=20, include_deleted=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if include_deleted:
        c.execute('''SELECT id, trans_date, type, amount, category, account, note, is_deleted
                     FROM transactions ORDER BY trans_date DESC LIMIT ?''', (limit,))
    else:
        c.execute('''SELECT id, trans_date, type, amount, category, account, note
                     FROM transactions WHERE is_deleted = 0 ORDER BY trans_date DESC LIMIT ?''', (limit,))
    rows = c.fetchall()
    conn.close()
    for row in rows:
        if len(row) == 8:
            id_, date, typ, amt, cat, acc, note, deleted = row
            status = " [已删除]" if deleted else ""
            print(f"{id_}: {date} | {typ} | {amt:.2f} | {cat} | {acc} | {note}{status}")
        else:
            id_, date, typ, amt, cat, acc, note = row
            print(f"{id_}: {date} | {typ} | {amt:.2f} | {cat} | {acc} | {note}")

def summary(year=None, month=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    where = "WHERE is_deleted = 0"
    params = []
    if year:
        where += " AND strftime('%Y', trans_date) = ?"
        params.append(str(year))
        if month:
            where += " AND strftime('%m', trans_date) = ?"
            params.append(f"{month:02d}")
    c.execute(f"SELECT type, SUM(amount) FROM transactions {where} GROUP BY type", params)
    rows = c.fetchall()
    conn.close()
    total_income = sum(amt for typ, amt in rows if typ == 'income' and amt)
    total_expense = sum(amt for typ, amt in rows if typ == 'expense' and amt)
    balance = total_income - total_expense
    period = f"{year or '所有'}-{month or '全年'}"
    print(f"📊 收支统计 ({period}):")
    print(f"  收入: {total_income:.2f}")
    print(f"  支出: {total_expense:.2f}")
    print(f"  结余: {balance:.2f}")

def update_transaction(tid, field, value):
    allowed_fields = ['amount', 'category', 'subcategory', 'account', 'project', 'member', 'merchant', 'note', 'trans_date']
    if field not in allowed_fields:
        print(f"❌ 不支持的字段: {field}")
        return
    if field == 'amount':
        value = float(value)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f'UPDATE transactions SET {field} = ? WHERE id = ? AND is_deleted = 0', (value, tid))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected:
        print(f"✅ 已更新 ID={tid} 的 {field} 为 {value}")
    else:
        print(f"❌ 未找到 ID={tid} 的有效交易（可能已删除或不存在）")

def soft_delete_transaction(tid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE transactions SET is_deleted = 1 WHERE id = ? AND is_deleted = 0', (tid,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected:
        print(f"✅ 已软删除 ID={tid} 的交易（可恢复）")
    else:
        print(f"❌ 未找到 ID={tid} 的有效交易或已删除")

def restore_transaction(tid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE transactions SET is_deleted = 0 WHERE id = ? AND is_deleted = 1', (tid,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected:
        print(f"✅ 已恢复 ID={tid} 的交易")
    else:
        print(f"❌ 未找到 ID={tid} 的已删除交易")

def hard_delete_transaction(tid, confirm=False):
    if not confirm:
        print("⚠️ 物理删除不可恢复，请添加 --confirm 参数确认")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM transactions WHERE id = ?', (tid,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected:
        print(f"✅ 已物理删除 ID={tid} 的交易")
    else:
        print(f"❌ 未找到 ID={tid} 的交易")

def set_budget(category, amount, year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO budgets (category, year, month, amount)
                 VALUES (?, ?, ?, ?)''', (category, year, month, amount))
    conn.commit()
    conn.close()
    print(f"✅ 预算已设置: {category} {year}-{month} 限额 {amount}")

def check_budget(year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT category, amount FROM budgets WHERE year=? AND month=?''', (year, month))
    budgets = {row[0]: row[1] for row in c.fetchall()}
    if not budgets:
        print("本月无预算")
        return
    for cat, budget in budgets.items():
        c.execute('''SELECT SUM(amount) FROM transactions
                     WHERE type='expense' AND category=? AND strftime('%Y', trans_date)=? AND strftime('%m', trans_date)=? AND is_deleted=0''',
                  (cat, str(year), f"{month:02d}"))
        spent = c.fetchone()[0] or 0
        remain = budget - spent
        print(f"{cat}: 预算 {budget:.2f}, 已用 {spent:.2f}, 剩余 {remain:.2f}")
    conn.close()

def import_csv(csv_file):
    if not os.path.exists(csv_file):
        print(f"❌ 文件不存在: {csv_file}")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    total, imported, skipped = 0, 0, 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            type_raw = row.get('交易类型', '').strip()
            if type_raw == '支出':
                tx_type = 'expense'
            elif type_raw == '收入':
                tx_type = 'income'
            else:
                skipped += 1
                continue
            try:
                amount = float(row.get('金额', 0))
            except:
                amount = 0.0
            if amount == 0:
                skipped += 1
                continue
            raw_date = row.get('日期', '').strip()
            if not raw_date:
                skipped += 1
                continue
            try:
                dt = datetime.strptime(raw_date, '%Y/%m/%d %H:%M')
                trans_date = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    dt = datetime.strptime(raw_date, '%Y/%m/%d')
                    trans_date = dt.strftime('%Y-%m-%d 00:00:00')
                except:
                    print(f"⚠️ 日期格式错误: {raw_date}")
                    skipped += 1
                    continue
            category = row.get('类别', '').strip()
            subcategory = row.get('子类别', '').strip()
            account = row.get('账户', '').strip()
            project = row.get('项目', '').strip()
            member = row.get('成员', '').strip()
            merchant = row.get('商家', '').strip()
            note = row.get('备注', '').strip()
            c.execute('''INSERT INTO transactions
                (type, amount, category, subcategory, account, project, member, merchant, note, trans_date, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''',
                (tx_type, amount, category, subcategory, account, project, member, merchant, note, trans_date))
            if account:
                c.execute('INSERT OR IGNORE INTO accounts (name) VALUES (?)', (account,))
            if member:
                c.execute('INSERT OR IGNORE INTO members (name) VALUES (?)', (member,))
            if project:
                c.execute('INSERT OR IGNORE INTO projects (name) VALUES (?)', (project,))
            imported += 1
    conn.commit()
    conn.close()
    print(f"✅ 导入完成: 总行 {total}, 成功 {imported}, 跳过 {skipped}")

def reconcile_guide():
    print("""
📘 数据矫正对账指南：
1. 导出银行/支付宝流水为CSV
2. 使用 import_csv 导入（注意去重，建议先备份数据库）
3. 或手动添加调整记录：`add -t expense/income -a 金额 -c 账务调整 -n "对账差异"`
4. 如需批量软删除错误记录，请先 list 查看ID，再使用 delete --id <ID>
5. 对于小额差异，可直接添加调整项并备注
    """)

def search_transactions(keyword, search_type='all', limit=50):
    """搜索交易记录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if search_type == 'all':
        c.execute('''SELECT id, trans_date, type, amount, category, account, note 
                     FROM transactions 
                     WHERE is_deleted = 0 AND (
                         note LIKE ? OR category LIKE ? OR subcategory LIKE ? OR 
                         merchant LIKE ? OR account LIKE ? OR project LIKE ? OR member LIKE ?
                     )
                     ORDER BY trans_date DESC LIMIT ?''',
                  (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', 
                   f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
    elif search_type == 'note':
        c.execute('''SELECT id, trans_date, type, amount, category, account, note 
                     FROM transactions 
                     WHERE is_deleted = 0 AND note LIKE ?
                     ORDER BY trans_date DESC LIMIT ?''',
                  (f'%{keyword}%', limit))
    elif search_type == 'category':
        c.execute('''SELECT id, trans_date, type, amount, category, account, note 
                     FROM transactions 
                     WHERE is_deleted = 0 AND (category LIKE ? OR subcategory LIKE ?)
                     ORDER BY trans_date DESC LIMIT ?''',
                  (f'%{keyword}%', f'%{keyword}%', limit))
    elif search_type == 'merchant':
        c.execute('''SELECT id, trans_date, type, amount, category, account, note 
                     FROM transactions 
                     WHERE is_deleted = 0 AND merchant LIKE ?
                     ORDER BY trans_date DESC LIMIT ?''',
                  (f'%{keyword}%', limit))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print(f"未找到包含 '{keyword}' 的交易记录")
        return
    
    print(f"找到 {len(rows)} 条相关记录：")
    for row in rows:
        id_, date, typ, amt, cat, acc, note = row
        print(f"{id_}: {date} | {typ} | {amt:.2f} | {cat} | {acc} | {note}")

def filter_transactions(category=None, account=None, member=None, merchant=None, 
                       project=None, start_date=None, end_date=None, limit=50):
    """按条件筛选交易记录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    where_clauses = ["is_deleted = 0"]
    params = []
    
    if category:
        where_clauses.append("(category = ? OR subcategory = ?)")
        params.extend([category, category])
    if account:
        where_clauses.append("account = ?")
        params.append(account)
    if member:
        where_clauses.append("member = ?")
        params.append(member)
    if merchant:
        where_clauses.append("merchant = ?")
        params.append(merchant)
    if project:
        where_clauses.append("project = ?")
        params.append(project)
    if start_date:
        where_clauses.append("trans_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("trans_date <= ?")
        params.append(end_date)
    
    where_sql = " AND ".join(where_clauses)
    c.execute(f'''SELECT id, trans_date, type, amount, category, account, note 
                 FROM transactions 
                 WHERE {where_sql}
                 ORDER BY trans_date DESC LIMIT ?''', 
              params + [limit])
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("未找到符合条件的交易记录")
        return
    
    print(f"找到 {len(rows)} 条记录：")
    for row in rows:
        id_, date, typ, amt, cat, acc, note = row
        print(f"{id_}: {date} | {typ} | {amt:.2f} | {cat} | {acc} | {note}")

def export_transactions(output_file, format_type='csv', category=None, start_date=None, end_date=None):
    """导出交易记录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    where_clauses = ["is_deleted = 0"]
    params = []
    
    if category:
        where_clauses.append("(category = ? OR subcategory = ?)")
        params.extend([category, category])
    if start_date:
        where_clauses.append("trans_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("trans_date <= ?")
        params.append(end_date)
    
    where_sql = " AND ".join(where_clauses)
    c.execute(f'''SELECT id, trans_date, type, amount, category, subcategory, 
                         account, project, member, merchant, note
                 FROM transactions 
                 WHERE {where_sql}
                 ORDER BY trans_date DESC''', params)
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("没有数据可导出")
        return False
    
    if format_type == 'csv':
        import csv
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', '日期', '类型', '金额', '类别', '子类别', '账户', '项目', '成员', '商家', '备注'])
            for row in rows:
                writer.writerow(row)
        print(f"已导出 {len(rows)} 条记录到 {output_file}")
        return True
    
    elif format_type == 'json':
        import json
        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'date': row[1],
                'type': row[2],
                'amount': row[3],
                'category': row[4],
                'subcategory': row[5],
                'account': row[6],
                'project': row[7],
                'member': row[8],
                'merchant': row[9],
                'note': row[10]
            })
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已导出 {len(rows)} 条记录到 {output_file}")
        return True
    
    print(f"不支持的导出格式: {format_type}")
    return False

def get_statistics(year=None, month=None, group_by='category'):
    """获取统计数据"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    where_clauses = ["is_deleted = 0"]
    params = []
    
    if year:
        where_clauses.append("strftime('%Y', trans_date) = ?")
        params.append(str(year))
    if month:
        where_clauses.append("strftime('%m', trans_date) = ?")
        params.append(f"{month:02d}")
    
    where_sql = " AND ".join(where_clauses)
    
    if group_by == 'category':
        c.execute(f'''SELECT category, type, SUM(amount), COUNT(*) 
                     FROM transactions 
                     WHERE {where_sql}
                     GROUP BY category, type
                     ORDER BY SUM(amount) DESC''', params)
    elif group_by == 'account':
        c.execute(f'''SELECT account, type, SUM(amount), COUNT(*) 
                     FROM transactions 
                     WHERE {where_sql}
                     GROUP BY account, type
                     ORDER BY SUM(amount) DESC''', params)
    elif group_by == 'month':
        c.execute(f'''SELECT strftime('%Y-%m', trans_date) as month, type, SUM(amount), COUNT(*) 
                     FROM transactions 
                     WHERE {where_sql}
                     GROUP BY month, type
                     ORDER BY month DESC''', params)
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("没有统计数据")
        return
    
    print(f"按{group_by}统计：")
    for row in rows:
        group, typ, total, count = row
        print(f"  {group} ({typ}): {total:.2f} 元, {count} 笔")

def list_accounts():
    """列出所有账户"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name FROM accounts ORDER BY name')
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("暂无账户数据")
        return
    
    print(f"所有账户 ({len(rows)} 个)：")
    for row in rows:
        print(f"  - {row[0]}")

def list_categories():
    """列出所有类别"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT category, subcategory, COUNT(*), SUM(amount) 
                 FROM transactions 
                 WHERE is_deleted = 0 
                 GROUP BY category, subcategory 
                 ORDER BY category, subcategory''')
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("暂无类别数据")
        return
    
    print("所有类别：")
    current_cat = None
    for row in rows:
        cat, subcat, count, total = row
        if cat != current_cat:
            current_cat = cat
            print(f"\n  {cat}:")
        if subcat:
            print(f"    - {subcat} ({count}笔, {total:.2f}元)")
        else:
            print(f"    - [无子类别] ({count}笔, {total:.2f}元)")

def list_members():
    """列出所有成员"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT member, type, COUNT(*), SUM(amount) 
                 FROM transactions 
                 WHERE is_deleted = 0 AND member != '' 
                 GROUP BY member, type 
                 ORDER BY member''')
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        print("暂无成员数据")
        return
    
    print("所有成员：")
    current_member = None
    for row in rows:
        member, typ, count, total = row
        if member != current_member:
            current_member = member
            print(f"\n  {member}:")
        print(f"    - {typ}: {count}笔, {total:.2f}元")

def main():
    parser = argparse.ArgumentParser(description="记账 API")
    parser.add_argument('action', choices=[
        'add', 'list', 'summary', 'update', 'delete', 'restore', 'hard_delete',
        'budget_set', 'budget_check', 'import_csv', 'reconcile_guide',
        'search', 'filter', 'export', 'stats', 'accounts', 'categories', 'members'
    ])
    parser.add_argument('--type', choices=['expense', 'income'])
    parser.add_argument('--amount', type=float)
    parser.add_argument('--category')
    parser.add_argument('--subcategory')
    parser.add_argument('--account')
    parser.add_argument('--project')
    parser.add_argument('--member')
    parser.add_argument('--merchant')
    parser.add_argument('--note')
    parser.add_argument('--date')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--year', type=int)
    parser.add_argument('--month', type=int)
    parser.add_argument('--id', type=int)
    parser.add_argument('--field')
    parser.add_argument('--value')
    parser.add_argument('--file')
    parser.add_argument('--confirm', action='store_true')
    parser.add_argument('--include_deleted', action='store_true')
    parser.add_argument('--keyword', help='搜索关键词')
    parser.add_argument('--search_type', choices=['all', 'note', 'category', 'merchant'], default='all')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv')
    parser.add_argument('--start_date', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end_date', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--group_by', choices=['category', 'account', 'month'], default='category')

    args = parser.parse_args()

    init_db()

    if args.action == 'add':
        if not args.type or not args.amount:
            print("❌ add 需要 --type 和 --amount")
            return
        add_transaction(args.type, args.amount, args.category, args.subcategory,
                        args.account, args.project, args.member, args.merchant,
                        args.note, args.date)
    elif args.action == 'list':
        list_transactions(args.limit, args.include_deleted)
    elif args.action == 'summary':
        summary(args.year, args.month)
    elif args.action == 'update':
        if not args.id or not args.field or args.value is None:
            print("❌ update 需要 --id, --field, --value")
            return
        update_transaction(args.id, args.field, args.value)
    elif args.action == 'delete':
        if not args.id:
            print("❌ delete 需要 --id")
            return
        soft_delete_transaction(args.id)
    elif args.action == 'restore':
        if not args.id:
            print("❌ restore 需要 --id")
            return
        restore_transaction(args.id)
    elif args.action == 'hard_delete':
        if not args.id:
            print("❌ hard_delete 需要 --id")
            return
        hard_delete_transaction(args.id, args.confirm)
    elif args.action == 'budget_set':
        if not args.category or args.amount is None:
            print("❌ budget_set 需要 --category 和 --amount")
            return
        set_budget(args.category, args.amount, args.year, args.month)
    elif args.action == 'budget_check':
        check_budget(args.year, args.month)
    elif args.action == 'import_csv':
        if not args.file:
            print("❌ import_csv 需要 --file")
            return
        import_csv(args.file)
    elif args.action == 'reconcile_guide':
        reconcile_guide()
    elif args.action == 'search':
        if not args.keyword:
            print("❌ search 需要 --keyword")
            return
        search_transactions(args.keyword, args.search_type, args.limit)
    elif args.action == 'filter':
        filter_transactions(args.category, args.account, args.member, args.merchant,
                           args.project, args.start_date, args.end_date, args.limit)
    elif args.action == 'export':
        if not args.output:
            print("❌ export 需要 --output")
            return
        export_transactions(args.output, args.format, args.category, args.start_date, args.end_date)
    elif args.action == 'stats':
        get_statistics(args.year, args.month, args.group_by)
    elif args.action == 'accounts':
        list_accounts()
    elif args.action == 'categories':
        list_categories()
    elif args.action == 'members':
        list_members()

if __name__ == "__main__":
    main()