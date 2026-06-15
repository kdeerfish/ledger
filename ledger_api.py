#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import csv
import sys
import argparse
import os
from datetime import datetime

import ledger_modules.db as db_module
import ledger_modules.transactions as transactions_module
import ledger_modules.budgets as budgets_module
from ledger_modules import (
    init_db as module_init_db,
    add_transaction as module_add_transaction,
    list_transactions as module_list_transactions,
    summary as module_summary,
    update_transaction as module_update_transaction,
    soft_delete_transaction as module_soft_delete_transaction,
    restore_transaction as module_restore_transaction,
    hard_delete_transaction as module_hard_delete_transaction,
    set_budget as module_set_budget,
    check_budget as module_check_budget,
    create_budget_template as module_create_budget_template,
    list_budget_templates as module_list_budget_templates,
    update_budget_template as module_update_budget_template,
    delete_budget_template as module_delete_budget_template,
    apply_budget_template as module_apply_budget_template,
    suggest_budget_templates as module_suggest_budget_templates,
    import_csv as module_import_csv,
    reconcile_guide as module_reconcile_guide,
    search_transactions as module_search_transactions,
    filter_transactions as module_filter_transactions,
    export_transactions as module_export_transactions,
    get_statistics as module_get_statistics,
    list_accounts as module_list_accounts,
    list_categories as module_list_categories,
    list_members as module_list_members,
)

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

def set_budget(category, amount, year=None, month=None, dimension_type='category', dimension_value=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    if not dimension_type:
        dimension_type = 'category'
    if dimension_type == 'category' and not dimension_value:
        dimension_value = category
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO budgets (category, year, month, amount, dimension_type, dimension_value)
                 VALUES (?, ?, ?, ?, ?, ?)''', (category, year, month, amount, dimension_type, dimension_value))
    conn.commit()
    conn.close()
    print(f"✅ 预算已设置: {category} {year}-{month} 限额 {amount} ({dimension_type}:{dimension_value or '-'})")


def _get_budget_spent(category, year, month, dimension_type='category', dimension_value=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    where_clauses = ["type='expense'", "strftime('%Y', trans_date)=?", "strftime('%m', trans_date)=?", "is_deleted=0"]
    params = [str(year), f"{month:02d}"]
    if category:
        where_clauses.append("category = ?")
        params.append(category)
    if dimension_type and dimension_type != 'category' and dimension_value:
        where_clauses.append(f"{dimension_type} = ?")
        params.append(dimension_value)
    c.execute(f'''SELECT COALESCE(SUM(amount), 0) FROM transactions
                   WHERE {' AND '.join(where_clauses)}''', params)
    spent = c.fetchone()[0] or 0
    conn.close()
    return float(spent)


def check_budget(year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT category, amount, dimension_type, dimension_value FROM budgets WHERE year=? AND month=? ORDER BY category''', (year, month))
    budgets = c.fetchall()
    conn.close()
    if not budgets:
        print("本月无预算")
        return
    for category, budget_amount, dimension_type, dimension_value in budgets:
        spent = _get_budget_spent(category, year, month, dimension_type, dimension_value)
        remain = budget_amount - spent
        suffix = f" | {dimension_type}:{dimension_value}" if dimension_type and dimension_type != 'category' and dimension_value else ""
        print(f"{category}{suffix}: 预算 {budget_amount:.2f}, 已用 {spent:.2f}, 剩余 {remain:.2f}")


def create_budget_template(name, description='', category=None, amount=0.0, dimension_type='category', dimension_value=None,
                           account=None, project=None, member=None, merchant=None, note=None, year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO budget_templates (
        name, description, category, amount, dimension_type, dimension_value,
        account, project, member, merchant, note, year, month, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, description, category, amount, dimension_type, dimension_value,
               account, project, member, merchant, note, year, month, created_at))
    template_id = c.lastrowid
    conn.commit()
    conn.close()
    return template_id


def list_budget_templates():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, name, description, category, amount, dimension_type, dimension_value,
                        account, project, member, merchant, note, year, month, created_at
                 FROM budget_templates ORDER BY created_at DESC''')
    rows = c.fetchall()
    conn.close()
    return [
        {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'category': row[3],
            'amount': row[4],
            'dimension_type': row[5],
            'dimension_value': row[6],
            'account': row[7],
            'project': row[8],
            'member': row[9],
            'merchant': row[10],
            'note': row[11],
            'year': row[12],
            'month': row[13],
            'created_at': row[14],
        }
        for row in rows
    ]


def update_budget_template(template_id, **kwargs):
    allowed_fields = ['name', 'description', 'category', 'amount', 'dimension_type', 'dimension_value',
                      'account', 'project', 'member', 'merchant', 'note', 'year', 'month']
    if not kwargs:
        return False
    updates = []
    values = []
    for field, value in kwargs.items():
        if field not in allowed_fields:
            continue
        updates.append(f"{field} = ?")
        values.append(value)
    if not updates:
        return False
    values.append(template_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f'UPDATE budget_templates SET {", ".join(updates)} WHERE id = ?', values)
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def delete_budget_template(template_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM budget_templates WHERE id = ?', (template_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def apply_budget_template(template_id, year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT name, category, amount, dimension_type, dimension_value,
                      account, project, member, merchant, note
                 FROM budget_templates WHERE id = ?''', (template_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    name, category, amount, dimension_type, dimension_value, account, project, member, merchant, note = row
    set_budget(category or name, amount or 0.0, year, month,
               dimension_type=dimension_type or 'category',
               dimension_value=dimension_value or None)
    return {'category': category or name, 'amount': amount, 'dimension_type': dimension_type or 'category', 'dimension_value': dimension_value}


def suggest_budget_templates(limit=3):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT category, account, member, project, merchant, COUNT(*) AS cnt, SUM(amount) AS total
                 FROM transactions
                 WHERE type='expense' AND is_deleted=0
                 GROUP BY category, account, member, project, merchant
                 HAVING COUNT(*) >= 2
                 ORDER BY cnt DESC, total DESC
                 LIMIT ?''', (limit,))
    rows = c.fetchall()
    conn.close()
    suggestions = []
    for category, account, member, project, merchant, cnt, total in rows:
        if not category and not account and not member and not project and not merchant:
            continue
        if account:
            dimension_type = 'account'
            dimension_value = account
        elif member:
            dimension_type = 'member'
            dimension_value = member
        elif project:
            dimension_type = 'project'
            dimension_value = project
        elif merchant:
            dimension_type = 'merchant'
            dimension_value = merchant
        else:
            dimension_type = 'category'
            dimension_value = category
        suggestions.append({
            'name': f"{category or '常用'}模板",
            'description': f"根据 {cnt} 笔相似记录自动生成",
            'category': category,
            'amount': round(float(total) / cnt, 2),
            'dimension_type': dimension_type,
            'dimension_value': dimension_value,
            'account': account,
            'member': member,
            'project': project,
            'merchant': merchant,
        })
    return suggestions

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
    """列出所有账户（从交易记录中提取）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT account FROM transactions WHERE is_deleted = 0 AND account != '' ORDER BY account")
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
    """列出所有成员（从交易记录中提取）"""
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
        'budget_set', 'budget_check', 'budget_template_create', 'budget_template_list',
        'budget_template_update', 'budget_template_delete', 'budget_template_apply',
        'budget_template_suggest', 'import_csv', 'reconcile_guide',
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
    parser.add_argument('--template_id', type=int)
    parser.add_argument('--template_name')
    parser.add_argument('--template_description')
    parser.add_argument('--dimension_type', choices=['category', 'account', 'member', 'project', 'merchant'])
    parser.add_argument('--dimension_value')
    parser.add_argument('--template_amount', type=float)
    parser.add_argument('--template_limit', type=int, default=3)

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
    elif args.action == 'budget_template_create':
        template_id = create_budget_template(
            args.template_name or '未命名模板',
            args.template_description or '',
            args.category,
            args.template_amount or 0.0,
            args.dimension_type or 'category',
            args.dimension_value,
            args.account,
            args.project,
            args.member,
            args.merchant,
            args.note,
            args.year,
            args.month,
        )
        print(f"✅ 已创建模板 ID={template_id}")
    elif args.action == 'budget_template_list':
        for item in list_budget_templates():
            print(f"{item['id']}: {item['name']} | {item['category']} | {item['amount']:.2f} | {item['dimension_type']}:{item['dimension_value'] or '-'}")
    elif args.action == 'budget_template_update':
        if not args.template_id:
            print("❌ budget_template_update 需要 --template_id")
            return
        kwargs = {}
        if args.template_name is not None:
            kwargs['name'] = args.template_name
        if args.template_description is not None:
            kwargs['description'] = args.template_description
        if args.category is not None:
            kwargs['category'] = args.category
        if args.template_amount is not None:
            kwargs['amount'] = args.template_amount
        if args.dimension_type is not None:
            kwargs['dimension_type'] = args.dimension_type
        if args.dimension_value is not None:
            kwargs['dimension_value'] = args.dimension_value
        if args.account is not None:
            kwargs['account'] = args.account
        if args.project is not None:
            kwargs['project'] = args.project
        if args.member is not None:
            kwargs['member'] = args.member
        if args.merchant is not None:
            kwargs['merchant'] = args.merchant
        if args.note is not None:
            kwargs['note'] = args.note
        if args.year is not None:
            kwargs['year'] = args.year
        if args.month is not None:
            kwargs['month'] = args.month
        success = update_budget_template(args.template_id, **kwargs)
        print("✅ 已更新模板" if success else "❌ 未找到模板")
    elif args.action == 'budget_template_delete':
        if not args.template_id:
            print("❌ budget_template_delete 需要 --template_id")
            return
        success = delete_budget_template(args.template_id)
        print("✅ 已删除模板" if success else "❌ 未找到模板")
    elif args.action == 'budget_template_apply':
        if not args.template_id:
            print("❌ budget_template_apply 需要 --template_id")
            return
        apply_budget_template(args.template_id, args.year, args.month)
    elif args.action == 'budget_template_suggest':
        for item in suggest_budget_templates(args.template_limit):
            print(f"建议: {item['name']} | 类目={item['category']} | 金额={item['amount']:.2f} | 维度={item['dimension_type']}:{item['dimension_value']}")
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