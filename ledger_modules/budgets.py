import sqlite3
from datetime import datetime

from .db import DB_PATH


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
    c.execute(f'''SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE {' AND '.join(where_clauses)}''', params)
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
    return [{
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
    } for row in rows]


def update_budget_template(template_id, **kwargs):
    allowed_fields = ['name', 'description', 'category', 'amount', 'dimension_type', 'dimension_value', 'account', 'project', 'member', 'merchant', 'note', 'year', 'month']
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
    c.execute('''SELECT name, category, amount, dimension_type, dimension_value
                 FROM budget_templates WHERE id = ?''', (template_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    name, category, amount, dimension_type, dimension_value = row
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
