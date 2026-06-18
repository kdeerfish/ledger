#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger Web 服务 - Flask 后端 API
在飞牛OS (FnOS) 上通过 Python3 + Flask 直接运行，无需 Docker
"""

import os
import sys
import json
from datetime import datetime
from functools import wraps

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module
from ledger_modules.config import get_db_path, load_env_file

# 加载 .env 配置
load_env_file()

# 数据库路径
DB_PATH = get_db_path()

def sync_db_path():
    """确保所有模块使用同一数据库路径"""
    db_module.DB_PATH = DB_PATH
    tx_module.DB_PATH = DB_PATH
    budget_module.DB_PATH = DB_PATH

sync_db_path()
db_module.init_db()

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)

# Web 配置
WEB_HOST = os.environ.get('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.environ.get('WEB_PORT', '5800'))
WEB_DEBUG = os.environ.get('WEB_DEBUG', '').lower() in ('true', '1', 'yes')


# ─── 辅助函数 ──────────────────────────────────────────

def api_error(msg, status=400):
    return jsonify({'success': False, 'error': msg}), status

def api_success(data=None, message=None):
    result = {'success': True}
    if data is not None:
        result['data'] = data
    if message:
        result['message'] = message
    return jsonify(result)


# ─── 页面路由 ──────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ─── 健康检查 ──────────────────────────────────────────

@app.route('/health')
@app.route('/api/health')
def health():
    """Docker 健康检查端点"""
    try:
        conn = db_module.sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions")
        count = c.fetchone()[0]
        conn.close()
        return jsonify({
            'status': 'ok',
            'database': DB_PATH,
            'records': count,
            'version': '1.4.0',
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ─── 交易 API ──────────────────────────────────────────

@app.route('/api/transactions', methods=['GET'])
def list_transactions():
    sync_db_path()
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    include_deleted = request.args.get('include_deleted', '').lower() in ('true', '1')

    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if include_deleted:
        c.execute('''SELECT id, trans_date, type, amount, category, subcategory, account,
                            project, member, merchant, note, is_deleted
                     FROM transactions ORDER BY trans_date DESC LIMIT ? OFFSET ?''', (limit, offset))
    else:
        c.execute('''SELECT id, trans_date, type, amount, category, subcategory, account,
                            project, member, merchant, note
                     FROM transactions WHERE is_deleted = 0 ORDER BY trans_date DESC LIMIT ? OFFSET ?''', (limit, offset))
    rows = c.fetchall()

    # 总记录数
    if include_deleted:
        c.execute("SELECT COUNT(*) FROM transactions")
    else:
        c.execute("SELECT COUNT(*) FROM transactions WHERE is_deleted = 0")
    total = c.fetchone()[0]
    conn.close()

    transactions = []
    for row in rows:
        t = {
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
            'note': row[10],
        }
        if len(row) > 11:
            t['is_deleted'] = bool(row[11])
        transactions.append(t)

    return api_success({'transactions': transactions, 'total': total})


@app.route('/api/transactions/<int:tid>', methods=['GET'])
def get_transaction(tid):
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, trans_date, type, amount, category, subcategory, account,
                        project, member, merchant, note, is_deleted
                 FROM transactions WHERE id = ?''', (tid,))
    row = c.fetchone()
    conn.close()
    if not row:
        return api_error('交易不存在', 404)
    return api_success({
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
        'note': row[10],
        'is_deleted': bool(row[11]),
    })


@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    sync_db_path()
    data = request.get_json()
    if not data:
        return api_error('请求数据不能为空')

    type_ = data.get('type', '支出')
    amount = data.get('amount')
    if amount is None:
        return api_error('金额不能为空')
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return api_error('金额格式不正确')

    category = data.get('category', '')
    subcategory = data.get('subcategory', '')
    account = data.get('account', '')
    project = data.get('project', '')
    member = data.get('member', '')
    merchant = data.get('merchant', '')
    note = data.get('note', '')
    trans_date = data.get('date')
    force = data.get('force', False)

    try:
        tx_module.DB_PATH = DB_PATH
        new_id = tx_module.add_transaction(
            type_, amount, category, subcategory,
            account, project, member, merchant,
            note, trans_date, force=force,
        )
        if new_id is None:
            return api_error('发现重复记录，请确认后重试（设置 force=true 强制添加）')
        return api_success({'id': new_id}, '添加成功')
    except Exception as e:
        return api_error(f'添加失败: {str(e)}')


@app.route('/api/transactions/<int:tid>', methods=['PUT'])
def update_transaction(tid):
    sync_db_path()
    data = request.get_json()
    if not data:
        return api_error('请求数据不能为空')

    field = data.get('field')
    value = data.get('value')
    if not field or value is None:
        return api_error('field 和 value 不能为空')

    allowed_fields = ['amount', 'category', 'subcategory', 'account',
                      'project', 'member', 'merchant', 'note', 'trans_date']
    if field not in allowed_fields:
        return api_error(f'不支持的字段: {field}，支持的字段: {", ".join(allowed_fields)}')

    try:
        tx_module.DB_PATH = DB_PATH
        tx_module.update_transaction(tid, field, value)
        return api_success(message='更新成功')
    except Exception as e:
        return api_error(f'更新失败: {str(e)}')


@app.route('/api/transactions/<int:tid>', methods=['DELETE'])
def delete_transaction(tid):
    sync_db_path()
    try:
        tx_module.DB_PATH = DB_PATH
        tx_module.soft_delete_transaction(tid)
        return api_success(message='删除成功')
    except Exception as e:
        return api_error(f'删除失败: {str(e)}')


@app.route('/api/transactions/<int:tid>/restore', methods=['POST'])
def restore_transaction(tid):
    sync_db_path()
    try:
        tx_module.DB_PATH = DB_PATH
        tx_module.restore_transaction(tid)
        return api_success(message='恢复成功')
    except Exception as e:
        return api_error(f'恢复失败: {str(e)}')


# ─── 搜索/筛选 API ─────────────────────────────────────

@app.route('/api/transactions/search', methods=['GET'])
def search_transactions():
    sync_db_path()
    keyword = request.args.get('keyword', '')
    search_type = request.args.get('search_type', 'all')
    limit = request.args.get('limit', 50, type=int)

    if not keyword:
        return api_error('搜索关键词不能为空')

    tx_module.DB_PATH = DB_PATH
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    params = []
    where = "is_deleted = 0 AND ("

    if search_type == 'all':
        fields = ['note', 'category', 'subcategory', 'merchant', 'account', 'project', 'member']
        clauses = [f"{f} LIKE ?" for f in fields]
        where += " OR ".join(clauses) + ")"
        params = [f'%{keyword}%'] * len(fields)
    elif search_type == 'note':
        where += "note LIKE ?)"
        params = [f'%{keyword}%']
    elif search_type == 'category':
        where += "(category LIKE ? OR subcategory LIKE ?))"
        params = [f'%{keyword}%', f'%{keyword}%']
    elif search_type == 'merchant':
        where += "merchant LIKE ?)"
        params = [f'%{keyword}%']

    c.execute(f'''SELECT id, trans_date, type, amount, category, account, note
                  FROM transactions WHERE {where} ORDER BY trans_date DESC LIMIT ?''',
              params + [limit])
    rows = c.fetchall()
    conn.close()

    return api_success([{
        'id': r[0], 'date': r[1], 'type': r[2], 'amount': r[3],
        'category': r[4], 'account': r[5], 'note': r[6],
    } for r in rows])


# ─── 统计/汇总 API ─────────────────────────────────────

@app.route('/api/summary', methods=['GET'])
def get_summary():
    sync_db_path()
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    conn = db_module.sqlite3.connect(DB_PATH)
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
    total_income = sum(amt for typ, amt in rows if typ == '收入' and amt)
    total_expense = sum(amt for typ, amt in rows if typ == '支出' and amt)
    balance = total_income - total_expense
    conn.close()

    return api_success({
        'income': total_income,
        'expense': total_expense,
        'balance': balance,
        'year': year,
        'month': month,
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    sync_db_path()
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    group_by = request.args.get('group_by', 'category')

    conn = db_module.sqlite3.connect(DB_PATH)
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
                     FROM transactions WHERE {where_sql} GROUP BY category, type ORDER BY SUM(amount) DESC''', params)
    elif group_by == 'account':
        c.execute(f'''SELECT account, type, SUM(amount), COUNT(*)
                     FROM transactions WHERE {where_sql} GROUP BY account, type ORDER BY SUM(amount) DESC''', params)
    elif group_by == 'month':
        c.execute(f'''SELECT strftime('%Y-%m', trans_date) as month, type, SUM(amount), COUNT(*)
                     FROM transactions WHERE {where_sql} GROUP BY month, type ORDER BY month DESC''', params)
    else:
        return api_error(f'不支持的分组: {group_by}')

    rows = c.fetchall()
    conn.close()

    items = []
    for row in rows:
        items.append({
            'group': row[0],
            'type': row[1],
            'total': row[2],
            'count': row[3],
        })

    return api_success({'group_by': group_by, 'items': items})


# ─── 类别/账户/成员 API ────────────────────────────────

@app.route('/api/categories', methods=['GET'])
def get_categories():
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT category, subcategory, COUNT(*), SUM(amount)
                 FROM transactions WHERE is_deleted = 0
                 GROUP BY category, subcategory ORDER BY category, subcategory''')
    rows = c.fetchall()
    conn.close()

    cats = {}
    for cat, subcat, count, total in rows:
        if cat not in cats:
            cats[cat] = {'name': cat, 'subcategories': [], 'total_count': 0, 'total_amount': 0}
        cats[cat]['subcategories'].append({
            'name': subcat or '(无子类别)',
            'count': count,
            'amount': total,
        })
        cats[cat]['total_count'] += count
        cats[cat]['total_amount'] += total

    return api_success(list(cats.values()))


@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT account, COUNT(*), SUM(amount)
                 FROM transactions WHERE is_deleted = 0 AND account != ''
                 GROUP BY account ORDER BY COUNT(*) DESC''')
    rows = c.fetchall()
    conn.close()
    return api_success([{'name': r[0], 'count': r[1], 'amount': r[2]} for r in rows])


@app.route('/api/members', methods=['GET'])
def get_members():
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT member, COUNT(*), SUM(amount)
                 FROM transactions WHERE is_deleted = 0 AND member != ''
                 GROUP BY member ORDER BY COUNT(*) DESC''')
    rows = c.fetchall()
    conn.close()
    return api_success([{'name': r[0], 'count': r[1], 'amount': r[2]} for r in rows])


# ─── 预算 API ──────────────────────────────────────────

@app.route('/api/budgets', methods=['GET'])
def list_budgets():
    sync_db_path()
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month

    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, category, year, month, amount, dimension_type, dimension_value
                 FROM budgets WHERE year=? AND month=? ORDER BY category''', (year, month))
    rows = c.fetchall()
    conn.close()

    items = []
    for row in rows:
        budget_id, category, byear, bmonth, amount, dim_type, dim_value = row
        spent = budget_module._get_budget_spent(category, byear, bmonth, dim_type, dim_value)
        items.append({
            'id': budget_id,
            'category': category,
            'year': byear,
            'month': bmonth,
            'amount': amount,
            'spent': spent,
            'remaining': amount - spent,
            'dimension_type': dim_type,
            'dimension_value': dim_value,
        })

    return api_success(items)


@app.route('/api/budgets', methods=['POST'])
def set_budget():
    sync_db_path()
    data = request.get_json()
    if not data:
        return api_error('请求数据不能为空')

    category = data.get('category', '')
    amount = data.get('amount')
    if category and amount is None:
        return api_error('类别和金额不能为空')
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return api_error('金额格式不正确')

    year = data.get('year') or datetime.now().year
    month = data.get('month') or datetime.now().month
    dim_type = data.get('dimension_type', 'category')
    dim_value = data.get('dimension_value')

    try:
        budget_module.DB_PATH = DB_PATH
        budget_module.set_budget(category, amount, year, month, dim_type, dim_value)
        return api_success(message='预算设置成功')
    except Exception as e:
        return api_error(f'设置失败: {str(e)}')


@app.route('/api/budgets/check', methods=['GET'])
def check_budget():
    sync_db_path()
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month

    budget_module.DB_PATH = DB_PATH
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, category, amount, dimension_type, dimension_value
                 FROM budgets WHERE year=? AND month=? ORDER BY category''', (year, month))
    budgets = c.fetchall()
    conn.close()

    items = []
    for row in budgets:
        bid, category, amount, dim_type, dim_value = row
        spent = budget_module._get_budget_spent(category, year, month, dim_type, dim_value)
        items.append({
            'id': bid,
            'category': category,
            'budget': amount,
            'spent': spent,
            'remaining': amount - spent,
            'percentage': round(spent / amount * 100, 1) if amount > 0 else 0,
        })

    return api_success(items)


# ─── 导出 API ──────────────────────────────────────────

@app.route('/api/export', methods=['GET'])
def export_data():
    sync_db_path()
    format_type = request.args.get('format', 'json')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if format_type not in ('json', 'csv'):
        return api_error('不支持的导出格式，仅支持 json/csv')

    conn = db_module.sqlite3.connect(DB_PATH)
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
    c.execute(f'''SELECT id, trans_date, type, amount, category, subcategory, account,
                        project, member, merchant, note
                 FROM transactions WHERE {where_sql} ORDER BY trans_date DESC''', params)
    rows = c.fetchall()
    conn.close()

    if not rows:
        return api_error('没有数据可导出')

    data = [{
        'id': r[0], 'date': r[1], 'type': r[2], 'amount': r[3],
        'category': r[4], 'subcategory': r[5], 'account': r[6],
        'project': r[7], 'member': r[8], 'merchant': r[9], 'note': r[10],
    } for r in rows]

    return api_success({'count': len(data), 'format': format_type, 'data': data})


# ─── 分析 API ──────────────────────────────────────────

@app.route('/api/analyze', methods=['GET'])
def analyze():
    sync_db_path()
    tx_module.DB_PATH = DB_PATH
    result = tx_module.analyze_data()
    return api_success({'report': result})


# ─── 数据库信息 API ────────────────────────────────────

@app.route('/api/info', methods=['GET'])
def db_info():
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM transactions")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM transactions WHERE is_deleted = 0")
    active = c.fetchone()[0]
    c.execute("SELECT MIN(trans_date) FROM transactions WHERE is_deleted = 0")
    oldest = c.fetchone()[0]
    c.execute("SELECT MAX(trans_date) FROM transactions WHERE is_deleted = 0")
    newest = c.fetchone()[0]
    conn.close()

    return api_success({
        'total_records': total,
        'active_records': active,
        'date_range': {'oldest': oldest, 'newest': newest},
        'db_path': DB_PATH,
    })


# ─── 启动入口 ──────────────────────────────────────────

if __name__ == '__main__':
    # 检测是否在 Docker 中运行
    in_docker = os.path.exists('/.dockerenv')

    msg = (
        "\n"
        + "=" * 50 + "\n"
        + " Ledger Web Service\n"
        + "=" * 50 + "\n"
        + "  Database: {}\n".format(DB_PATH)
        + "  Address:  http://{}:{}\n".format(WEB_HOST, WEB_PORT)
        + ("  Mode:     Docker\n" if in_docker else "  Mode:     Native\n")
        + "  Press Ctrl+C to stop\n"
        + "=" * 50 + "\n"
    )
    print(msg, flush=True)
    app.run(host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG)
