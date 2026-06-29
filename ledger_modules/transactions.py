import csv
import json
import os
import sqlite3
from datetime import datetime

from .db import DB_PATH, init_db, ensure_account, recalc_account_balances, get_account_balance, get_account_balances_with_type, get_net_worth


def _safe_print(*args, **kwargs):
    """安全打印，处理 Windows GBK 编码问题"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        try:
            out = ' '.join(str(a) for a in args)
            print(out.encode('ascii', 'replace').decode('ascii'), **kwargs)
        except Exception:
            pass


def _infer_account_type(name):
    """根据账户名简单推断账户类型"""
    if not name:
        return 'self'
    name_lower = name.lower()
    liability_keywords = ['信用卡', '信用ka', '银行ka', '借记卡', '欠款', '负债']
    claims_keywords = ['借出', '应收', '债权', '借款']
    for kw in liability_keywords:
        if kw in name:
            return 'liability'
    for kw in claims_keywords:
        if kw in name:
            return 'claims'
    return 'self'


def check_duplicate(type_, amount, category, account, trans_date=None, from_account=None, to_account=None):
    """
    检查是否存在相似的重复记录
    
    检查条件：同一天 + 同类型 + 同金额 + 同类别 + 同账户/双账户
    
    返回：相似记录列表，如果无重复返回空列表
    """
    if trans_date is None:
        trans_date = datetime.now().strftime('%Y-%m-%d')
    
    # 只取日期部分（去掉时间）
    date_part = trans_date.split(' ')[0] if ' ' in trans_date else trans_date
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 构建查询条件
    conditions = ["is_deleted = 0", "type = ?", "amount = ?", "category = ?", "strftime('%Y-%m-%d', trans_date) = ?"]
    params = [type_, amount, category, date_part]
    
    # 账户匹配：优先用 from_account/to_account，回退到 account
    account_conditions = []
    if from_account:
        account_conditions.append("from_account = ?")
        account_conditions.append("to_account = ?")
        params.extend([from_account, from_account])
    if to_account:
        account_conditions.append("from_account = ?")
        account_conditions.append("to_account = ?")
        params.extend([to_account, to_account])
    if account:
        account_conditions.append("account = ?")
        params.append(account)
    
    if account_conditions:
        conditions.append(f"({' OR '.join(account_conditions)})")
    
    sql = f'''SELECT id, trans_date, type, amount, category, account, from_account, to_account, note 
              FROM transactions 
              WHERE {' AND '.join(conditions)}'''
    c.execute(sql, params)
    
    rows = c.fetchall()
    conn.close()
    
    return [{
        'id': row[0],
        'date': row[1],
        'type': row[2],
        'amount': row[3],
        'category': row[4],
        'account': row[5],
        'from_account': row[6],
        'to_account': row[7],
        'note': row[8]
    } for row in rows]


def add_transaction(type_, amount, category, subcategory, account, project, member, merchant, note, trans_date=None, force=False, from_account=None, to_account=None, ensure_accounts=True):
    """
    添加交易记录
    
    参数：
        force: 如果为 True，跳过重复检查直接插入
        from_account: 转出账户
        to_account: 转入账户
        ensure_accounts: 是否自动创建不存在的账户
    """
    if trans_date is None:
        trans_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 确定账户字段
    if not from_account and not to_account and account:
        from_account = account
        to_account = account
    
    # 自动创建账户
    if ensure_accounts:
        for acc in [from_account, to_account]:
            if acc:
                acc_type = _infer_account_type(acc)
                ensure_account(acc, account_type=acc_type)
    
    # 重复检查（除非 force=True）
    if not force:
        duplicates = check_duplicate(type_, amount, category, account, trans_date, from_account, to_account)
        if duplicates:
            _safe_print(f"⚠️ 发现 {len(duplicates)} 条相似记录：")
            for d in duplicates:
                _safe_print(f"  ID={d['id']}: {d['date']} | {d['type']} | {d['amount']:.2f} | {d['category']} | {d['from_account']}->{d['to_account']} | {d['note']}")
            _safe_print("如需强制插入，请添加 --confirm 参数")
            return None
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO transactions
        (type, amount, category, subcategory, account, from_account, to_account, project, member, merchant, note, trans_date, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''',
        (type_, amount, category, subcategory, account, from_account, to_account, project, member, merchant, note, trans_date))
    new_id = c.lastrowid
    
    # 重新计算涉及账户的余额
    account_names = set()
    if from_account:
        account_names.add(from_account)
    if to_account:
        account_names.add(to_account)
    if account:
        account_names.add(account)
    recalc_account_balances(conn, account_names)
    
    conn.commit()
    conn.close()
    _safe_print(f"✅ 已添加记录 ID={new_id}: {type_} {amount} 元 | {category} | {from_account or account} -> {to_account or account or ''}")
    return new_id


def list_transactions(limit=20, include_deleted=False, account=None, from_account=None, to_account=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    where_clauses = ["1=1"]
    params = []
    
    if not include_deleted:
        where_clauses.append("is_deleted = 0")
    
    if account:
        where_clauses.append("account = ?")
        params.append(account)
    if from_account:
        where_clauses.append("from_account = ?")
        params.append(from_account)
    if to_account:
        where_clauses.append("to_account = ?")
        params.append(to_account)
    
    sql = f'''SELECT id, trans_date, type, amount, category, account, from_account, to_account, note, is_deleted
              FROM transactions 
              WHERE {' AND '.join(where_clauses)}
              ORDER BY trans_date DESC LIMIT ?'''
    params.append(limit)
    
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    
    for row in rows:
        id_, date, typ, amt, cat, acc, from_acc, to_acc, note, deleted = row
        status = " [已删除]" if deleted else ""
        if from_acc and to_acc and from_acc != to_acc:
            display = f"{from_acc} -> {to_acc}"
        else:
            display = acc or from_acc or to_acc or ''
        _safe_print(f"{id_}: {date} | {typ} | {amt:.2f} | {cat} | {display} | {note}{status}")


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

    from .transaction_types import (
        is_stat_expense,
        is_stat_income,
        is_transfer,
    )
    total_income = sum(amt for typ, amt in rows if is_stat_income(typ) and amt)
    total_expense = sum(amt for typ, amt in rows if is_stat_expense(typ) and amt)
    total_transfer = sum(amt for typ, amt in rows if is_transfer(typ) and amt)
    balance = total_income - total_expense
    period = f"{year or '所有'}-{month or '全年'}"
    _safe_print(f"📊 收支统计 ({period}):")
    _safe_print(f"  收入: {total_income:.2f}")
    _safe_print(f"  支出: {total_expense:.2f}")
    _safe_print(f"  转账: {total_transfer:.2f}")
    _safe_print(f"  结余: {balance:.2f}")


def update_transaction(tid, field, value):
    allowed_fields = ['amount', 'category', 'subcategory', 'account', 'project', 'member', 'merchant', 'note', 'trans_date', 'from_account', 'to_account']
    if field not in allowed_fields:
        _safe_print(f"❌ 不支持的字段: {field}")
        return
    if field == 'amount':
        value = float(value)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 如果更新账户相关字段，重新计算余额
    account_names = set()
    if field in ('account', 'from_account', 'to_account'):
        c.execute("SELECT from_account, to_account, account FROM transactions WHERE id = ? AND is_deleted = 0", (tid,))
        old = c.fetchone()
        if old:
            for acc in old:
                if acc:
                    account_names.add(acc)
    
    c.execute(f'UPDATE transactions SET {field} = ? WHERE id = ? AND is_deleted = 0', (value, tid))
    conn.commit()
    affected = c.rowcount
    
    if affected and field in ('account', 'from_account', 'to_account'):
        if value:
            account_names.add(value)
        if account_names:
            recalc_account_balances(conn, account_names)
            conn.commit()
    
    conn.close()
    if affected:
        _safe_print(f"✅ 已更新 ID={tid} 的 {field} 为 {value}")
    else:
        _safe_print(f"❌ 未找到 ID={tid} 的有效交易（可能已删除或不存在）")


def soft_delete_transaction(tid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取交易涉及的账户
    c.execute("SELECT from_account, to_account, account FROM transactions WHERE id = ? AND is_deleted = 0", (tid,))
    row = c.fetchone()
    account_names = set()
    if row:
        for acc in row:
            if acc:
                account_names.add(acc)
    
    c.execute('UPDATE transactions SET is_deleted = 1 WHERE id = ? AND is_deleted = 0', (tid,))
    conn.commit()
    affected = c.rowcount
    
    if affected and account_names:
        recalc_account_balances(conn, account_names)
        conn.commit()
    
    conn.close()
    if affected:
        _safe_print(f"✅ 已软删除 ID={tid} 的交易（可恢复）")
    else:
        _safe_print(f"❌ 未找到 ID={tid} 的有效交易或已删除")


def restore_transaction(tid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取交易涉及的账户
    c.execute("SELECT from_account, to_account, account FROM transactions WHERE id = ? AND is_deleted = 1", (tid,))
    row = c.fetchone()
    account_names = set()
    if row:
        for acc in row:
            if acc:
                account_names.add(acc)
    
    c.execute('UPDATE transactions SET is_deleted = 0 WHERE id = ? AND is_deleted = 1', (tid,))
    conn.commit()
    affected = c.rowcount
    
    if affected and account_names:
        recalc_account_balances(conn, account_names)
        conn.commit()
    
    conn.close()
    if affected:
        _safe_print(f"✅ 已恢复 ID={tid} 的交易")
    else:
        _safe_print(f"❌ 未找到 ID={tid} 的已删除交易")


def hard_delete_transaction(tid, confirm=False):
    if not confirm:
        _safe_print("⚠️ 物理删除不可恢复，请添加 --confirm 参数确认")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取交易涉及的账户
    c.execute("SELECT from_account, to_account, account FROM transactions WHERE id = ?", (tid,))
    row = c.fetchone()
    account_names = set()
    if row:
        for acc in row:
            if acc:
                account_names.add(acc)
    
    c.execute('DELETE FROM transactions WHERE id = ?', (tid,))
    conn.commit()
    affected = c.rowcount
    
    if affected and account_names:
        recalc_account_balances(conn, account_names)
        conn.commit()
    
    conn.close()
    if affected:
        _safe_print(f"✅ 已物理删除 ID={tid} 的交易")
    else:
        _safe_print(f"❌ 未找到 ID={tid} 的交易")


def import_csv(csv_file):
    """
    向后兼容的 CSV 导入函数

    内部转调 import_engine.import_csv_compat()
    """
    from . import import_engine
    import_engine.DB_PATH = DB_PATH
    return import_engine.import_csv_compat(csv_file)


def reconcile_guide():
    _safe_print("""
📘 数据矫正对账指南：
1. 导出银行/支付宝流水为CSV
2. 使用 import_csv 导入（注意去重，建议先备份数据库）
3. 或手动添加调整记录：`add -t 支出/收入 -a 金额 -c 账务调整 -n "对账差异"`
4. 如需批量软删除错误记录，请先 list 查看ID，再使用 delete --id <ID>
5. 对于小额差异，可直接添加调整项并备注
    """)


def search_transactions(keyword, search_type='all', limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if search_type == 'all':
        c.execute('''SELECT id, trans_date, type, amount, category, account, from_account, to_account, note
                     FROM transactions
                     WHERE is_deleted = 0 AND (
                         note LIKE ? OR category LIKE ? OR subcategory LIKE ? OR
                         merchant LIKE ? OR account LIKE ? OR from_account LIKE ? OR to_account LIKE ? OR
                         project LIKE ? OR member LIKE ?
                     )
                     ORDER BY trans_date DESC LIMIT ?''',
                  (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
    elif search_type == 'note':
        c.execute('''SELECT id, trans_date, type, amount, category, account, from_account, to_account, note
                     FROM transactions
                     WHERE is_deleted = 0 AND note LIKE ?
                     ORDER BY trans_date DESC LIMIT ?''', (f'%{keyword}%', limit))
    elif search_type == 'category':
        c.execute('''SELECT id, trans_date, type, amount, category, account, from_account, to_account, note
                     FROM transactions
                     WHERE is_deleted = 0 AND (category LIKE ? OR subcategory LIKE ?)
                     ORDER BY trans_date DESC LIMIT ?''', (f'%{keyword}%', f'%{keyword}%', limit))
    elif search_type == 'merchant':
        c.execute('''SELECT id, trans_date, type, amount, category, account, from_account, to_account, note
                     FROM transactions
                     WHERE is_deleted = 0 AND merchant LIKE ?
                     ORDER BY trans_date DESC LIMIT ?''', (f'%{keyword}%', limit))
    rows = c.fetchall()
    conn.close()
    if not rows:
        _safe_print(f"未找到包含 '{keyword}' 的交易记录")
        return
    _safe_print(f"找到 {len(rows)} 条相关记录：")
    for row in rows:
        id_, date, typ, amt, cat, acc, from_acc, to_acc, note = row
        if from_acc and to_acc and from_acc != to_acc:
            display = f"{from_acc} -> {to_acc}"
        else:
            display = acc or from_acc or to_acc or ''
        _safe_print(f"{id_}: {date} | {typ} | {amt:.2f} | {cat} | {display} | {note}")


def filter_transactions(category=None, account=None, member=None, merchant=None, project=None, start_date=None, end_date=None, limit=50, from_account=None, to_account=None):
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
    if from_account:
        where_clauses.append("from_account = ?")
        params.append(from_account)
    if to_account:
        where_clauses.append("to_account = ?")
        params.append(to_account)
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
    c.execute(f'''SELECT id, trans_date, type, amount, category, account, from_account, to_account, note FROM transactions WHERE {where_sql} ORDER BY trans_date DESC LIMIT ?''', params + [limit])
    rows = c.fetchall()
    conn.close()
    if not rows:
        _safe_print("未找到符合条件的交易记录")
        return
    _safe_print(f"找到 {len(rows)} 条记录：")
    for row in rows:
        id_, date, typ, amt, cat, acc, from_acc, to_acc, note = row
        if from_acc and to_acc and from_acc != to_acc:
            display = f"{from_acc} -> {to_acc}"
        else:
            display = acc or from_acc or to_acc or ''
        _safe_print(f"{id_}: {date} | {typ} | {amt:.2f} | {cat} | {display} | {note}")


def export_transactions(output_file, format_type='csv', category=None, start_date=None, end_date=None):
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
    c.execute(f'''SELECT id, trans_date, type, amount, category, subcategory, account, from_account, to_account, project, member, merchant, note FROM transactions WHERE {where_sql} ORDER BY trans_date DESC''', params)
    rows = c.fetchall()
    conn.close()
    if not rows:
        _safe_print("没有数据可导出")
        return False
    if format_type == 'csv':
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', '日期', '类型', '金额', '类别', '子类别', '账户', '转出账户', '转入账户', '项目', '成员', '商家', '备注'])
            for row in rows:
                writer.writerow(row)
        _safe_print(f"已导出 {len(rows)} 条记录到 {output_file}")
        return True
    if format_type == 'json':
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
                'from_account': row[7],
                'to_account': row[8],
                'project': row[9],
                'member': row[10],
                'merchant': row[11],
                'note': row[12]
            })
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _safe_print(f"已导出 {len(rows)} 条记录到 {output_file}")
        return True
    _safe_print(f"不支持的导出格式: {format_type}")
    return False


def get_statistics(year=None, month=None, group_by='category'):
    """获取统计数据，返回格式化的字符串"""
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
        c.execute(f'''SELECT category, type, SUM(amount), COUNT(*) FROM transactions WHERE {where_sql} GROUP BY category, type ORDER BY SUM(amount) DESC''', params)
    elif group_by == 'account':
        c.execute(f'''SELECT COALESCE(account, from_account, to_account) as acc, type, SUM(amount), COUNT(*) FROM transactions WHERE {where_sql} GROUP BY acc, type ORDER BY SUM(amount) DESC''', params)
    elif group_by == 'from_account':
        c.execute(f'''SELECT from_account, type, SUM(amount), COUNT(*) FROM transactions WHERE {where_sql} GROUP BY from_account, type ORDER BY SUM(amount) DESC''', params)
    elif group_by == 'to_account':
        c.execute(f'''SELECT to_account, type, SUM(amount), COUNT(*) FROM transactions WHERE {where_sql} GROUP BY to_account, type ORDER BY SUM(amount) DESC''', params)
    elif group_by == 'month':
        c.execute(f'''SELECT strftime('%Y-%m', trans_date) as month, type, SUM(amount), COUNT(*) FROM transactions WHERE {where_sql} GROUP BY month, type ORDER BY month DESC''', params)
    else:
        c.execute(f'''SELECT category, type, SUM(amount), COUNT(*) FROM transactions WHERE {where_sql} GROUP BY category, type ORDER BY SUM(amount) DESC''', params)
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    # 构建结果
    result_lines = []
    if year and month:
        result_lines.append(f"{year}年{month}月 统计（按{group_by}）：")
    elif year:
        result_lines.append(f"{year}年 统计（按{group_by}）：")
    else:
        result_lines.append(f"统计（按{group_by}）：")
    
    # 汇总
    total_income = 0
    total_expense = 0
    
    for row in rows:
        group, typ, total, count = row
        if typ == '收入':
            total_income += total
        else:
            total_expense += total
        result_lines.append(f"  {group} ({typ}): {total:.2f} 元, {count} 笔")
    
    result_lines.append(f"\n汇总：收入 {total_income:.2f} 元，支出 {total_expense:.2f} 元，结余 {total_income - total_expense:.2f} 元")
    
    return "\n".join(result_lines)


def list_accounts():
    """列出所有账户，包含余额"""
    accounts = get_account_balances_with_type()
    if not accounts:
        _safe_print("暂无账户数据")
        return
    
    _safe_print(f"所有账户 ({len(accounts)} 个)：")
    for acc in accounts:
        type_label = {
            'self': '我的账户',
            'claims': '债权',
            'liability': '负债',
            'counterparty': '对手方'
        }.get(acc['account_type'], acc['account_type'])
        _safe_print(f"  - {acc['name']} ({type_label}): 余额 {acc['balance']:.2f} 元")


def list_categories():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT category, subcategory, COUNT(*), SUM(amount) FROM transactions WHERE is_deleted = 0 GROUP BY category, subcategory ORDER BY category, subcategory''')
    rows = c.fetchall()
    conn.close()
    if not rows:
        _safe_print("暂无类别数据")
        return
    _safe_print("所有类别：")
    current_cat = None
    for row in rows:
        cat, subcat, count, total = row
        if cat != current_cat:
            current_cat = cat
            _safe_print(f"\n  {cat}:")
        if subcat:
            _safe_print(f"    - {subcat} ({count}笔, {total:.2f}元)")
        else:
            _safe_print(f"    - [无子类别] ({count}笔, {total:.2f}元)")


def list_members():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT member, type, COUNT(*), SUM(amount) FROM transactions WHERE is_deleted = 0 AND member != '' GROUP BY member, type ORDER BY member''')
    rows = c.fetchall()
    conn.close()
    if not rows:
        _safe_print("暂无成员数据")
        return
    _safe_print("所有成员：")
    current_member = None
    for row in rows:
        member, typ, count, total = row
        if member != current_member:
            current_member = member
            _safe_print(f"\n  {member}:")
        _safe_print(f"    - {typ}: {count}笔, {total:.2f}元")


def analyze_data():
    """
    分析数据库中的用户数据，输出结构化摘要供 agent 学习。
    使用交叉聚合查询，让 agent 学到字段间的关系。
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    output = []
    output.append("═══════════════════════════════════════════════════")
    output.append("📊 用户数据分析报告（供 agent 学习用）")
    output.append("═══════════════════════════════════════════════════")
    
    # 1. 基本统计
    c.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE is_deleted=0")
    total_count, total_amount = c.fetchone()
    output.append(f"\n【总览】共 {total_count or 0} 笔记录，总金额 {total_amount or 0:.2f} 元")
    
    # 2. 按类型统计
    c.execute("SELECT type, COUNT(*), SUM(amount) FROM transactions WHERE is_deleted=0 GROUP BY type")
    rows = c.fetchall()
    output.append("\n【收支类型】")
    for typ, count, amount in rows:
        output.append(f"  {typ}: {count}笔 {amount:.2f}元")
    
    # 3. 账户列表（双账户视角）
    output.append("\n【账户】（转出账户 -> 转入账户）")
    c.execute('''SELECT from_account, to_account, COUNT(*), SUM(amount) 
                 FROM transactions WHERE is_deleted=0 
                 GROUP BY from_account, to_account ORDER BY COUNT(*) DESC''')
    rows = c.fetchall()
    for from_acc, to_acc, count, amount in rows:
        output.append(f"  {from_acc or ''} -> {to_acc or ''}: {count}笔 {amount:.2f}元")
    
    # 4. 商家列表
    c.execute('''SELECT merchant, COUNT(*), SUM(amount) 
                 FROM transactions WHERE is_deleted=0 AND merchant != '' 
                 GROUP BY merchant ORDER BY COUNT(*) DESC''')
    rows = c.fetchall()
    output.append("\n【商家】（在哪里花的钱）")
    for merchant, count, amount in rows:
        output.append(f"  {merchant}: {count}笔 {amount:.2f}元")
    
    # 5. 类别→子类别层级
    c.execute('''SELECT category, subcategory, COUNT(*), SUM(amount) 
                 FROM transactions WHERE is_deleted=0 
                 GROUP BY category, subcategory 
                 ORDER BY category, COUNT(*) DESC''')
    rows = c.fetchall()
    output.append("\n【类别→子类别】")
    current_cat = None
    for cat, subcat, count, amount in rows:
        if cat != current_cat:
            current_cat = cat
            output.append(f"\n  {cat}:")
        if subcat:
            output.append(f"    - {subcat} ({count}笔 {amount:.2f}元)")
        else:
            output.append(f"    - [无子类别] ({count}笔 {amount:.2f}元)")
    
    # 6. 账户余额
    output.append("\n【账户余额】")
    balances = get_account_balances_with_type()
    for b in balances:
        output.append(f"  {b['name']} ({b['account_type']}): 余额 {b['balance']:.2f} 元")
    
    # 净资产
    net = get_net_worth()
    output.append(f"\n净资产：{net:.2f} 元")
    
    # 7. 字段空值率
    c.execute("SELECT COUNT(*) FROM transactions WHERE is_deleted=0")
    total = c.fetchone()[0] or 1
    
    fields_to_check = ['account', 'from_account', 'to_account', 'merchant', 'project', 'member', 'subcategory', 'note']
    output.append("\n【字段使用率】")
    for field in fields_to_check:
        c.execute(f"SELECT COUNT(*) FROM transactions WHERE is_deleted=0 AND {field} != '' AND {field} IS NOT NULL")
        filled = c.fetchone()[0]
        rate = filled / total * 100
        output.append(f"  {field}: {filled}/{total} ({rate:.1f}%)")
    
    output.append("\n═══════════════════════════════════════════════════")
    
    conn.close()
    
    result = "\n".join(output)
    return result
