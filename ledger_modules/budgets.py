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
    where_clauses = ["type='支出'", "strftime('%Y', trans_date)=?", "strftime('%m', trans_date)=?", "is_deleted=0"]
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


def create_budget_template(name, description='', dimension_type='category', dimension_value=None, amount=0.0,
                           category=None, account=None, project=None, member=None, merchant=None, note=None, year=None, month=None):
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
    # When dimension_type is 'category', use dimension_value as the budget category
    if dimension_type == 'category' and dimension_value:
        budget_category = dimension_value
    else:
        budget_category = category or name
    set_budget(budget_category, amount or 0.0, year, month,
               dimension_type=dimension_type or 'category',
               dimension_value=dimension_value or None)
    return {'category': budget_category, 'amount': amount, 'dimension_type': dimension_type or 'category', 'dimension_value': dimension_value}


def suggest_budget_templates(limit=3):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT category, account, member, project, merchant, COUNT(*) AS cnt, SUM(amount) AS total
                 FROM transactions
                 WHERE type='支出' AND is_deleted=0
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


# ═══════════════════════════════════════════════════════════════════════════════
# 通用记录模板 CRUD
# ═══════════════════════════════════════════════════════════════════════════════


def create_record_template(name, template_type='通用', type_=None, amount=0.0,
                           category=None, subcategory=None, account=None, project=None,
                           member=None, merchant=None, note=None, description=''):
    """创建通用记录模板"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO record_templates 
        (name, description, template_type, type, amount, category, subcategory,
         account, project, member, merchant, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, description, template_type, type_, amount, category, subcategory,
               account, project, member, merchant, note, created_at))
    template_id = c.lastrowid
    conn.commit()
    conn.close()
    return template_id


def list_record_templates(template_type=None):
    """列出所有记录模板"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if template_type:
        c.execute('''SELECT id, name, description, template_type, type, amount, category, subcategory,
                            account, project, member, merchant, note, usage_count, last_used_at, created_at
                     FROM record_templates WHERE template_type = ? ORDER BY usage_count DESC, created_at DESC''',
                  (template_type,))
    else:
        c.execute('''SELECT id, name, description, template_type, type, amount, category, subcategory,
                            account, project, member, merchant, note, usage_count, last_used_at, created_at
                     FROM record_templates ORDER BY usage_count DESC, created_at DESC''')
    rows = c.fetchall()
    conn.close()
    return [{
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'template_type': row[3],
        'type': row[4],
        'amount': row[5],
        'category': row[6],
        'subcategory': row[7],
        'account': row[8],
        'project': row[9],
        'member': row[10],
        'merchant': row[11],
        'note': row[12],
        'usage_count': row[13],
        'last_used_at': row[14],
        'created_at': row[15],
    } for row in rows]


def get_record_template(template_id):
    """获取单个记录模板"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, name, description, template_type, type, amount, category, subcategory,
                        account, project, member, merchant, note, usage_count, last_used_at, created_at
                 FROM record_templates WHERE id = ?''', (template_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'template_type': row[3],
        'type': row[4],
        'amount': row[5],
        'category': row[6],
        'subcategory': row[7],
        'account': row[8],
        'project': row[9],
        'member': row[10],
        'merchant': row[11],
        'note': row[12],
        'usage_count': row[13],
        'last_used_at': row[14],
        'created_at': row[15],
    }


def update_record_template(template_id, **kwargs):
    """更新记录模板"""
    allowed_fields = ['name', 'description', 'template_type', 'type', 'amount', 'category', 
                      'subcategory', 'account', 'project', 'member', 'merchant', 'note']
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
    c.execute(f'UPDATE record_templates SET {", ".join(updates)} WHERE id = ?', values)
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def delete_record_template(template_id):
    """删除记录模板"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM record_templates WHERE id = ?', (template_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def apply_record_template(template_id, amount_override=None):
    """
    应用记录模板，返回模板数据供调用方使用
    
    参数：
        template_id: 模板ID
        amount_override: 如果提供，覆盖模板中的金额
    
    返回：
        模板数据字典，如果模板不存在返回 None
    """
    template = get_record_template(template_id)
    if not template:
        return None
    
    # 更新使用次数
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''UPDATE record_templates 
                 SET usage_count = usage_count + 1, last_used_at = ?
                 WHERE id = ?''', (now, template_id))
    conn.commit()
    conn.close()
    
    # 如果提供了金额覆盖，使用新金额
    if amount_override is not None:
        template['amount'] = amount_override
    
    return template


def suggest_record_templates(limit=5):
    """基于历史记录推荐模板"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 按类别、账户、成员、商家分组，找出常用组合
    c.execute('''SELECT type, category, subcategory, account, member, merchant, 
                        COUNT(*) AS cnt, AVG(amount) AS avg_amount
                 FROM transactions
                 WHERE is_deleted=0
                 GROUP BY type, category, subcategory, account, member, merchant
                 HAVING COUNT(*) >= 2
                 ORDER BY cnt DESC
                 LIMIT ?''', (limit,))
    
    rows = c.fetchall()
    conn.close()
    
    suggestions = []
    for row in rows:
        type_, category, subcategory, account, member, merchant, cnt, avg_amount = row
        
        # 确定模板类型
        if type_ == '支出':
            template_type = '支出'
        elif type_ == '收入':
            template_type = '收入'
        else:
            template_type = '通用'
        
        # 生成模板名称
        name_parts = []
        if category:
            name_parts.append(category)
        if subcategory:
            name_parts.append(subcategory)
        if not name_parts:
            name_parts.append('常用')
        name = f"{''.join(name_parts)}模板"
        
        suggestions.append({
            'name': name,
            'description': f"根据 {cnt} 笔相似记录自动生成",
            'template_type': template_type,
            'type': type_,
            'amount': round(float(avg_amount), 2),
            'category': category,
            'subcategory': subcategory,
            'account': account,
            'member': member,
            'merchant': merchant,
        })
    
    return suggestions
