#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger Web 服务 - Flask 后端 API (v2)
增强版：支持 Tags、Templates、多维统计、自动建议
"""

import os
import sys
import json
import urllib.request
from datetime import datetime
from functools import wraps

# 修复 Windows GBK 编码问题
if sys.platform == 'win32':
    try:
        if sys.stdout is not None:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr is not None:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    os.environ['PYTHONUTF8'] = '1'

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module
import ledger_modules.import_engine as import_engine
import ledger_modules.export_engine as export_engine
from ledger_modules.config import get_db_path, load_env_file

load_env_file()
DB_PATH = get_db_path()


def sync_db_path():
    db_module.DB_PATH = DB_PATH
    tx_module.DB_PATH = DB_PATH
    budget_module.DB_PATH = DB_PATH


sync_db_path()
db_module.init_db()

app = Flask(__name__, static_folder=None)


# ─── _method 覆盖中间件（WSGI 层，在路由匹配之前执行）───
class MethodOverrideMiddleware:
    """支持 ?_method=PUT/DELETE，兼容 wget 等不支持 PUT/DELETE 的客户端"""
    def __init__(self, wsgi_app):
        self.app = wsgi_app

    def __call__(self, environ, start_response):
        if environ.get('REQUEST_METHOD') == 'POST':
            from urllib.parse import parse_qs
            qs = parse_qs(environ.get('QUERY_STRING', ''))
            method = qs.get('_method', [''])[0].upper()
            if method in ('PUT', 'DELETE', 'PATCH'):
                environ['REQUEST_METHOD'] = method
                del qs['_method']
                environ['QUERY_STRING'] = '&'.join(
                    f'{k}={v[0]}' for k, v in qs.items()
                ) if qs else ''
        return self.app(environ, start_response)


app.wsgi_app = MethodOverrideMiddleware(app.wsgi_app)

# CORS
cors_origins = os.environ.get('WEB_CORS_ORIGINS', '').strip()
if cors_origins:
    CORS(app, origins=[o.strip() for o in cors_origins.split(',') if o.strip()], supports_credentials=True)
else:
    CORS(app, resources={r"/api/*": {"origins": []}})

WEB_HOST = os.environ.get('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.environ.get('WEB_PORT', '5800'))
WEB_DEBUG = os.environ.get('WEB_DEBUG', '').lower() in ('true', '1', 'yes')




def _get_version():
    try:
        import tomllib
        pyproject = os.path.join(ROOT_DIR, 'pyproject.toml')
        with open(pyproject, 'rb') as f:
            return tomllib.load(f).get('project', {}).get('version', '0.0.0')
    except Exception:
        return '0.0.0'




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


def get_exclude_clause(exclude_tagged, table_alias='t'):
    """
    返回排除"排除统计"标签的 SQL 子句和额外参数

    返回 (clause, extra_params)
    clause 为空字符串表示不排除
    """
    if not exclude_tagged:
        return '', []
    clause = f""" AND {table_alias}.id NOT IN (
        SELECT tt.transaction_id FROM transaction_tags tt
        JOIN tags tg ON tt.tag_id = tg.id
        WHERE tg.name = '排除统计'
    )"""
    return clause, []


def require_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        data = request.get_json(silent=True)
        if data is None:
            return api_error('请求数据不能为空（需要 JSON body）')
        return f(data, *args, **kwargs)
    return wrapper


def parse_date_params():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return year, month, start_date, end_date


def build_time_where(params, date_field='trans_date'):
    """构建时间筛选 WHERE 子句"""
    year, month, start_date, end_date = parse_date_params()
    clauses = []
    if year:
        clauses.append(f"strftime('%Y', {date_field}) = ?")
        params.append(str(year))
        if month:
            clauses.append(f"strftime('%m', {date_field}) = ?")
            params.append(f"{month:02d}")
    if start_date:
        clauses.append(f"{date_field} >= ?")
        params.append(start_date)
    if end_date:
        clauses.append(f"{date_field} <= ?")
        params.append(end_date)
    return clauses


# ─── 页面路由 ──────────────────────────────────────────

VITE_DEV_URL = 'http://localhost:5173'


def _proxy_to_vite(path=''):
    """调试模式下代理到 Vite 开发服务器，获得热更新"""
    try:
        url = f'{VITE_DEV_URL}/{path}' if path else f'{VITE_DEV_URL}/'
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=3)
        headers = dict(resp.headers)
        content = resp.read()
        # 去掉 Transfer-Encoding 让 Flask 自己处理
        headers.pop('Transfer-Encoding', None)
        headers.pop('Content-Encoding', None)
        return (content, resp.status, headers)
    except Exception:
        return None


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # API 请求不在此处理
    if path.startswith('api/'):
        return api_error('Not found', 404)

    # 调试模式：代理到 Vite dev server → 获得热更新
    if WEB_DEBUG:
        result = _proxy_to_vite(path)
        if result:
            return result

    # 生产模式：服务构建好的前端
    dist_dir = os.path.join(ROOT_DIR, 'frontend', 'dist')
    full_path = os.path.join(dist_dir, path) if path else os.path.join(dist_dir, 'index.html')

    # 如果请求的是具体文件且存在，直接返回
    if path and os.path.isfile(full_path):
        return send_from_directory(dist_dir, path)

    # 否则返回 index.html（React 路由处理）
    dist_index = os.path.join(dist_dir, 'index.html')
    if os.path.exists(dist_index):
        return send_from_directory(dist_dir, 'index.html')

    # 最后 fallback 到旧模板
    return render_template('index.html')


@app.route('/api/health')
@app.route('/health')
def health():
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
            'version': _get_version(),
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/quit', methods=['POST'])
def quit_app():
    """退出整个应用（仅限本地访问）"""
    import threading
    def _delayed_quit():
        import time
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=_delayed_quit, daemon=True).start()
    return jsonify({'success': True, 'message': 'Ledger 正在退出...'})


@app.route('/settings')
def settings_page():
    """设置页面"""
    settings_file = os.path.join(ROOT_DIR, 'frontend', 'settings.html')
    if os.path.exists(settings_file):
        return send_from_directory(os.path.dirname(settings_file), 'settings.html')
    return 'Settings page not found', 404


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取桌面配置"""
    try:
        from ledger_modules import desktop_config
        cfg = desktop_config.get()
        # 附加只读信息
        cfg['_config_file'] = desktop_config.CONFIG_FILE
        cfg['_version'] = _get_version()
        cfg['_db_path'] = os.environ.get('LEDGER_DB_PATH', '')
        cfg['_autostart'] = desktop_config.get_autostart_status()
        return jsonify(cfg)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['POST'])
def save_config():
    """保存桌面配置"""
    try:
        from ledger_modules import desktop_config
        data = request.get_json()
        desktop_config.update(data)
        desktop_config.save()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config/reset', methods=['POST'])
def reset_config():
    """恢复默认配置"""
    try:
        from ledger_modules import desktop_config
        desktop_config.reset()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/autostart', methods=['POST'])
def set_autostart():
    """设置开机自启"""
    try:
        from ledger_modules import desktop_config
        data = request.get_json()
        enable = data.get('enable', False)
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(sys.argv[0])
        ok, msg = desktop_config.set_autostart_windows(enable, exe_path)
        if ok:
            desktop_config.set('auto_start', enable)
            desktop_config.save()
        return jsonify({'success': ok, 'error': msg if not ok else None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pick-folder', methods=['POST'])
def pick_folder():
    """打开系统文件夹选择对话框，返回选中的路径"""
    import subprocess
    try:
        # 使用 PowerShell 调用 Windows 原生文件夹选择对话框
        ps_script = (
            'Add-Type -AssemblyName System.Windows.Forms; '
            '$f = New-Object System.Windows.Forms.FolderBrowserDialog; '
            '$f.Description = "选择数据库存放文件夹"; '
            '$f.ShowNewFolderButton = $true; '
            'if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { '
            '  $f.SelectedPath '
            '} else { '
            '  "CANCEL" '
            '}'
        )
        # CREATE_NO_WINDOW 隐藏 PowerShell 黑窗
        CREATE_NO_WINDOW = 0x08000000
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True, text=True, timeout=60,
            creationflags=CREATE_NO_WINDOW,
        )
        path = result.stdout.strip()
        if path and path != 'CANCEL':
            return jsonify({'success': True, 'path': path})
        return jsonify({'success': False, 'error': '用户取消'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ════════════════════════════════════════════════════════
# 交易 API
# ════════════════════════════════════════════════════════

@app.route('/api/transactions', methods=['GET'])
def list_transactions():
    sync_db_path()
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    include_deleted = request.args.get('include_deleted', '').lower() in ('true', '1')
    type_filter = request.args.get('type', '')
    category_filter = request.args.get('category', '')
    subcategory_filter = request.args.get('subcategory', '')
    account_filter = request.args.get('account', '')
    project_filter = request.args.get('project', '')
    member_filter = request.args.get('member', '')
    merchant_filter = request.args.get('merchant', '')
    tag_ids = request.args.get('tag_ids', '')
    keyword = request.args.get('keyword', '')

    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()

    where_clauses = []
    params = []

    if not include_deleted:
        where_clauses.append("t.is_deleted = 0")

    if type_filter:
        where_clauses.append("t.type = ?")
        params.append(type_filter)
    if category_filter:
        where_clauses.append("(t.category = ? OR t.subcategory = ?)")
        params.extend([category_filter, category_filter])
    if subcategory_filter:
        where_clauses.append("t.subcategory = ?")
        params.append(subcategory_filter)
    if account_filter:
        where_clauses.append("t.account = ?")
        params.append(account_filter)
    if project_filter:
        where_clauses.append("t.project = ?")
        params.append(project_filter)
    if member_filter:
        where_clauses.append("t.member = ?")
        params.append(member_filter)
    if merchant_filter:
        where_clauses.append("t.merchant = ?")
        params.append(merchant_filter)
    if keyword:
        where_clauses.append("(t.note LIKE ? OR t.category LIKE ? OR t.subcategory LIKE ? OR t.merchant LIKE ? OR t.account LIKE ?)")
        kw = f'%{keyword}%'
        params.extend([kw, kw, kw, kw, kw])

    # 时间筛选
    time_clauses = build_time_where(params, 't.trans_date')
    where_clauses.extend(time_clauses)

    # Tag 筛选
    if tag_ids:
        tag_list = [int(x) for x in tag_ids.split(',') if x.strip().isdigit()]
        if tag_list:
            placeholders = ','.join(['?'] * len(tag_list))
            where_clauses.append(f"t.id IN (SELECT transaction_id FROM transaction_tags WHERE tag_id IN ({placeholders}))")
            params.extend(tag_list)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # 排序
    sort_by = request.args.get('sort_by', 'trans_date')
    sort_order = request.args.get('sort_order', 'DESC').upper()
    allowed_sorts = {'trans_date', 'amount', 'type', 'category', 'account', 'merchant'}
    if sort_by not in allowed_sorts:
        sort_by = 'trans_date'
    if sort_order not in ('ASC', 'DESC'):
        sort_order = 'DESC'
    sort_col = f"t.{sort_by}"

    # 总数
    c.execute(f"SELECT COUNT(*) FROM transactions t WHERE {where_sql}", params)
    total = c.fetchone()[0]

    c.execute(f'''SELECT t.id, t.trans_date, t.type, t.amount, t.category, t.subcategory,
                        t.account, t.project, t.member, t.merchant, t.note
                 FROM transactions t
                 WHERE {where_sql}
                 ORDER BY {sort_col} {sort_order} LIMIT ? OFFSET ?''', params + [limit, offset])
    rows = c.fetchall()

    transactions = []
    for row in rows:
        t = {
            'id': row[0], 'date': row[1], 'type': row[2], 'amount': row[3],
            'category': row[4], 'subcategory': row[5], 'account': row[6],
            'project': row[7], 'member': row[8], 'merchant': row[9], 'note': row[10],
        }
        # 获取标签
        t['tags'] = db_module.get_transaction_tags(t['id'])
        transactions.append(t)

    conn.close()
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
    t = {
        'id': row[0], 'date': row[1], 'type': row[2], 'amount': row[3],
        'category': row[4], 'subcategory': row[5], 'account': row[6],
        'project': row[7], 'member': row[8], 'merchant': row[9],
        'note': row[10], 'is_deleted': bool(row[11]),
    }
    t['tags'] = db_module.get_transaction_tags(tid)
    return api_success(t)


@app.route('/api/transactions', methods=['POST'])
@require_json
def add_transaction(data):
    sync_db_path()
    type_ = data.get('type', '支出')
    amount = data.get('amount')
    if amount is None:
        return api_error('金额不能为空')
    try:
        amount = float(amount)
        if amount <= 0:
            return api_error('金额必须为正数')
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
    tag_ids = data.get('tag_ids', [])

    try:
        tx_module.DB_PATH = DB_PATH
        new_id = tx_module.add_transaction(
            type_, amount, category, subcategory,
            account, project, member, merchant,
            note, trans_date, force=force,
        )
        if new_id is None:
            return api_error('发现重复记录，请确认后重试（设置 force=true 强制添加）')
        # 设置标签
        if tag_ids:
            db_module.set_transaction_tags(new_id, tag_ids)
        return api_success({'id': new_id}, '添加成功')
    except Exception as e:
        return api_error(f'添加失败: {str(e)}')


@app.route('/api/transactions/<int:tid>', methods=['PUT'])
@require_json
def update_transaction(data, tid):
    sync_db_path()

    # 支持批量更新
    if 'field' in data and 'value' in data:
        # 单字段更新（向后兼容）
        field = data.get('field')
        value = data.get('value')
        allowed_fields = ['amount', 'category', 'subcategory', 'account',
                          'project', 'member', 'merchant', 'note', 'trans_date']
        if field not in allowed_fields:
            return api_error(f'不支持的字段: {field}')
        try:
            tx_module.DB_PATH = DB_PATH
            tx_module.update_transaction(tid, field, value)
            return api_success(message='更新成功')
        except Exception as e:
            return api_error(f'更新失败: {str(e)}')
    else:
        # 全字段更新
        update_fields = {}
        for f in ['type', 'amount', 'category', 'subcategory', 'account',
                  'project', 'member', 'merchant', 'note', 'trans_date']:
            if f in data:
                update_fields[f] = data[f]
        if 'date' in data and 'trans_date' not in update_fields:
            update_fields['trans_date'] = data['date']

        # Tag 更新
        tag_updated = False
        if 'tag_ids' in data:
            db_module.set_transaction_tags(tid, data['tag_ids'])
            tag_updated = True

        if not update_fields and not tag_updated:
            return api_error('没有需要更新的字段')

        try:
            tx_module.DB_PATH = DB_PATH
            for field, value in update_fields.items():
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


# ── 搜索兼容端点（旧版 test 仍用 /api/transactions/search）─
@app.route('/api/transactions/search', methods=['GET'])
def search_transactions_compat():
    """向后兼容的搜索端点"""
    sync_db_path()
    keyword = request.args.get('keyword', '')
    search_type = request.args.get('search_type', 'all')
    limit = request.args.get('limit', 50, type=int)

    if not keyword:
        return api_error('搜索关键词不能为空')

    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    params = []
    where = "is_deleted = 0 AND ("

    fields = ['note', 'category', 'subcategory', 'merchant', 'account', 'project', 'member']
    if search_type == 'all':
        clauses = [f"{f} LIKE ?" for f in fields]
        where += " OR ".join(clauses) + ")"
        params = [f'%{keyword}%'] * len(fields)
    elif search_type == 'note':
        where += "note LIKE ?)" + " AND is_deleted = 0"
        params = [f'%{keyword}%']
    elif search_type == 'category':
        where += "(category LIKE ? OR subcategory LIKE ?))"
        params = [f'%{keyword}%', f'%{keyword}%']
    elif search_type == 'merchant':
        where += "merchant LIKE ?)" + " AND is_deleted = 0"
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


# ════════════════════════════════════════════════════════
# Tags API
# ════════════════════════════════════════════════════════

@app.route('/api/tags', methods=['GET'])
def list_tags():
    tags = db_module.get_all_tags()
    # 附加使用次数
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for tag in tags:
        c.execute("SELECT COUNT(*) FROM transaction_tags WHERE tag_id = ?", (tag['id'],))
        tag['usage_count'] = c.fetchone()[0]
    conn.close()
    return api_success(tags)


@app.route('/api/tags', methods=['POST'])
@require_json
def create_tag(data):
    name = data.get('name', '').strip()
    if not name:
        return api_error('标签名称不能为空')
    color = data.get('color', '#6366f1')
    tag_id = db_module.create_tag(name, color)
    if tag_id:
        return api_success({'id': tag_id}, '标签创建成功')
    return api_error('创建标签失败')


@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    db_module.delete_tag(tag_id)
    return api_success(message='标签已删除')


@app.route('/api/tags/<int:tag_id>/transactions', methods=['GET'])
def list_tag_transactions(tag_id):
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    txs = db_module.get_transactions_by_tag(tag_id, limit, offset)
    return api_success(txs)


# ════════════════════════════════════════════════════════
# 模板 API (record_templates)
# ════════════════════════════════════════════════════════

@app.route('/api/templates', methods=['GET'])
def list_templates():
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, name, description, template_type, type, amount,
                        category, subcategory, account, project, member, merchant,
                        note, usage_count, last_used_at, tags
                 FROM record_templates ORDER BY usage_count DESC, name''')
    rows = c.fetchall()
    conn.close()
    items = []
    for r in rows:
        item = {
            'id': r[0], 'name': r[1], 'description': r[2], 'template_type': r[3],
            'type': r[4], 'amount': r[5], 'category': r[6], 'subcategory': r[7],
            'account': r[8], 'project': r[9], 'member': r[10], 'merchant': r[11],
            'note': r[12], 'usage_count': r[13], 'last_used_at': r[14],
            'tag_names': r[15].split(',') if r[15] else [],
        }
        items.append(item)
    return api_success(items)


@app.route('/api/templates', methods=['POST'])
@require_json
def create_template(data):
    name = data.get('name', '').strip()
    if not name:
        return api_error('模板名称不能为空')
    template_type = data.get('template_type', '通用')
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO record_templates
        (name, description, template_type, type, amount, category, subcategory,
         account, project, member, merchant, note, tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, data.get('description', ''), template_type,
               data.get('type', '支出'), data.get('amount', 0),
               data.get('category', ''), data.get('subcategory', ''),
               data.get('account', ''), data.get('project', ''),
               data.get('member', ''), data.get('merchant', ''),
               data.get('note', ''),
               ','.join(data.get('tag_names', [])), now))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return api_success({'id': new_id}, '模板创建成功')


@app.route('/api/templates/<int:tid>', methods=['PUT'])
@require_json
def update_template(data, tid):
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    sets = []
    params = []
    fields = ['name', 'description', 'template_type', 'type', 'amount',
              'category', 'subcategory', 'account', 'project', 'member', 'merchant', 'note']
    for f in fields:
        if f in data:
            sets.append(f"{f}=?")
            params.append(data[f])
    if 'tag_names' in data:
        sets.append("tags=?")
        params.append(','.join(data['tag_names']))
    if sets:
        params.append(tid)
        c.execute(f"UPDATE record_templates SET {', '.join(sets)} WHERE id=?", params)
        conn.commit()
    conn.close()
    return api_success(message='模板更新成功')


@app.route('/api/templates/<int:tid>', methods=['DELETE'])
def delete_template(tid):
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM record_templates WHERE id=?", (tid,))
    conn.commit()
    conn.close()
    return api_success(message='模板已删除')


@app.route('/api/templates/<int:tid>/use', methods=['POST'])
def use_template(tid):
    """使用模板（增加使用次数）"""
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("UPDATE record_templates SET usage_count=usage_count+1, last_used_at=? WHERE id=?",
              (now, tid))
    conn.commit()
    conn.close()
    return api_success(message='ok')


# ════════════════════════════════════════════════════════
# 自动建议 API
# ════════════════════════════════════════════════════════

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """获取自动建议数据：类别、子类别、账户、商家、项目、成员"""
    sync_db_path()
    field = request.args.get('field', 'all')
    keyword = request.args.get('keyword', '').strip()
    limit = request.args.get('limit', 20, type=int)
    if limit > 500:
        limit = 500

    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()

    result = {}

    fields_map = {
        'categories': ('category', 'category'),
        'subcategories': ('subcategory', 'subcategory'),
        'accounts': ('account', 'account'),
        'merchants': ('merchant', 'merchant'),
        'projects': ('project', 'project'),
        'members': ('member', 'member'),
    }

    for key, (db_col, _) in fields_map.items():
        if field != 'all' and field != key:
            continue
        # 获取隐藏列表
        hidden = _get_hidden(db_col)
        where = "WHERE is_deleted = 0 AND {} != '' AND {} IS NOT NULL".format(db_col, db_col)
        params = []
        if keyword:
            where += f" AND {db_col} LIKE ?"
            params.append(f'%{keyword}%')
        if hidden:
            placeholders = ','.join(['?'] * len(hidden))
            where += f" AND {db_col} NOT IN ({placeholders})"
            params.extend(hidden)
        c.execute(f'''SELECT {db_col}, COUNT(*), SUM(amount)
                     FROM transactions {where}
                     GROUP BY {db_col}
                     ORDER BY COUNT(*) DESC
                     LIMIT ?''', params + [limit])
        rows = c.fetchall()
        result[key] = [{'name': r[0], 'count': r[1], 'amount': r[2]} for r in rows]

    # 常用（使用次数最多的前5个）
    if field == 'all':
        result['frequent'] = {}
        for key, (db_col, _) in fields_map.items():
            freq_hidden = _get_hidden(db_col)
            freq_where = f"WHERE is_deleted = 0 AND {db_col} != '' AND {db_col} IS NOT NULL"
            freq_params = []
            if freq_hidden:
                ph = ','.join(['?'] * len(freq_hidden))
                freq_where += f" AND {db_col} NOT IN ({ph})"
                freq_params.extend(freq_hidden)
            c.execute(f'''SELECT {db_col}, COUNT(*)
                         FROM transactions
                         {freq_where}
                         GROUP BY {db_col}
                         ORDER BY COUNT(*) DESC
                         LIMIT 5''', freq_params)
            result['frequent'][key] = [{'name': r[0], 'count': r[1]} for r in c.fetchall()]

    conn.close()
    return api_success(result)


# ════════════════════════════════════════════════════════
# 摘要/统计 API (增强版)
# ════════════════════════════════════════════════════════

@app.route('/api/summary', methods=['GET'])
def get_summary():
    sync_db_path()
    year, month, start_date, end_date = parse_date_params()
    exclude_tagged = request.args.get('exclude_tagged', 'false').lower() == 'true'

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
    if start_date:
        where += " AND trans_date >= ?"
        params.append(start_date)
    if end_date:
        where += " AND trans_date <= ?"
        params.append(end_date)

    # 排除标记交易
    if exclude_tagged:
        where += """ AND id NOT IN (
            SELECT tt.transaction_id FROM transaction_tags tt
            JOIN tags tg ON tt.tag_id = tg.id WHERE tg.name = '排除统计'
        )"""

    c.execute(f"SELECT type, SUM(amount), COUNT(*) FROM transactions {where} GROUP BY type", params)
    rows = c.fetchall()
    total_income = sum(amt for typ, amt, cnt in rows if typ == '收入' and amt)
    total_expense = sum(amt for typ, amt, cnt in rows if typ == '支出' and amt)
    income_count = sum(cnt for typ, amt, cnt in rows if typ == '收入' and amt)
    expense_count = sum(cnt for typ, amt, cnt in rows if typ == '支出' and amt)

    # 日均支出
    if year and month:
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
    elif year:
        days_in_month = 365
    else:
        days_in_month = (datetime.now() - datetime(2000, 1, 1)).days or 1
    daily_avg = round(total_expense / days_in_month, 2) if days_in_month > 0 else 0

    conn.close()
    return api_success({
        'income': total_income or 0,
        'expense': total_expense or 0,
        'balance': (total_income or 0) - (total_expense or 0),
        'income_count': income_count,
        'expense_count': expense_count,
        'total_count': income_count + expense_count,
        'daily_avg_expense': daily_avg,
        'year': year,
        'month': month,
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    sync_db_path()
    year, month, start_date, end_date = parse_date_params()
    group_by = request.args.get('group_by', 'category')
    sub_group = request.args.get('sub_group', '')
    exclude_tagged = request.args.get('exclude_tagged', 'false').lower() == 'true'

    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    where_clauses = ["t.is_deleted = 0"]
    params = []
    time_clauses = build_time_where(params, 't.trans_date')
    where_clauses.extend(time_clauses)

    # 排除标记交易
    if exclude_tagged:
        where_clauses.append("""t.id NOT IN (
            SELECT tt.transaction_id FROM transaction_tags tt
            JOIN tags tg ON tt.tag_id = tg.id WHERE tg.name = '排除统计'
        )""")

    where_sql = " AND ".join(where_clauses)

    if group_by == 'category':
        if sub_group == 'subcategory':
            c.execute(f'''SELECT t.category, t.subcategory, t.type, SUM(t.amount), COUNT(*)
                         FROM transactions t WHERE {where_sql}
                         GROUP BY t.category, t.subcategory, t.type
                         ORDER BY t.category, SUM(t.amount) DESC''', params)
        else:
            c.execute(f'''SELECT t.category, t.type, SUM(t.amount), COUNT(*)
                         FROM transactions t WHERE {where_sql}
                         GROUP BY t.category, t.type ORDER BY SUM(t.amount) DESC''', params)
    elif group_by == 'subcategory':
        c.execute(f'''SELECT t.subcategory, t.type, SUM(t.amount), COUNT(*)
                     FROM transactions t WHERE {where_sql} AND t.subcategory != ''
                     GROUP BY t.subcategory, t.type ORDER BY SUM(t.amount) DESC''', params)
    elif group_by == 'account':
        c.execute(f'''SELECT t.account, t.type, SUM(t.amount), COUNT(*)
                     FROM transactions t WHERE {where_sql}
                     GROUP BY t.account, t.type ORDER BY SUM(t.amount) DESC''', params)
    elif group_by == 'merchant':
        c.execute(f'''SELECT t.merchant, t.type, SUM(t.amount), COUNT(*)
                     FROM transactions t WHERE {where_sql} AND t.merchant != ''
                     GROUP BY t.merchant, t.type ORDER BY SUM(t.amount) DESC''', params)
    elif group_by == 'project':
        c.execute(f'''SELECT t.project, t.type, SUM(t.amount), COUNT(*)
                     FROM transactions t WHERE {where_sql} AND t.project != ''
                     GROUP BY t.project, t.type ORDER BY SUM(t.amount) DESC''', params)
    elif group_by == 'member':
        c.execute(f'''SELECT t.member, t.type, SUM(t.amount), COUNT(*)
                     FROM transactions t WHERE {where_sql} AND t.member != ''
                     GROUP BY t.member, t.type ORDER BY SUM(t.amount) DESC''', params)
    elif group_by == 'month':
        c.execute(f'''SELECT strftime('%Y-%m', t.trans_date) as month, t.type, SUM(t.amount), COUNT(*)
                     FROM transactions t WHERE {where_sql}
                     GROUP BY month, t.type ORDER BY month DESC''', params)
    elif group_by == 'tag':
        c.execute(f'''SELECT tg.name, tg.color, SUM(t.amount), COUNT(*)
                     FROM transactions t
                     JOIN transaction_tags tt ON t.id = tt.transaction_id
                     JOIN tags tg ON tt.tag_id = tg.id
                     WHERE {where_sql}
                     GROUP BY tg.id ORDER BY SUM(t.amount) DESC''', params)
        rows = c.fetchall()
        conn.close()
        items = [{'group': r[0], 'color': r[1], 'type': '支出', 'total': r[2], 'count': r[3]} for r in rows]
        return api_success({'group_by': group_by, 'items': items})
    elif group_by == 'type':
        c.execute(f'''SELECT t.type, SUM(t.amount), COUNT(*)
                     FROM transactions t WHERE {where_sql}
                     GROUP BY t.type''', params)
        rows = c.fetchall()
        conn.close()
        items = [{'group': r[0], 'type': r[0], 'total': r[1], 'count': r[2]} for r in rows]
        return api_success({'group_by': group_by, 'items': items})
    else:
        conn.close()
        return api_error(f'不支持的分组: {group_by}')

    rows = c.fetchall()
    conn.close()

    if sub_group == 'subcategory':
        items = []
        for row in rows:
            cat, subcat, typ, total, count = row
            items.append({
                'group': f"{cat}/{subcat}" if subcat else cat,
                'parent_group': cat,
                'sub_group': subcat,
                'type': typ, 'total': total, 'count': count,
            })
    else:
        items = []
        for row in rows:
            items.append({
                'group': row[0], 'type': row[1], 'total': row[2], 'count': row[3],
            })

    return api_success({'group_by': group_by, 'items': items})


# ─── 趋势 API ──────────────────────────────────────────

@app.route('/api/trends', methods=['GET'])
def get_trends():
    """获取趋势数据（日/周/月粒度）"""
    sync_db_path()
    year = request.args.get('year', type=int) or datetime.now().year
    granularity = request.args.get('granularity', 'month')
    exclude_tagged = request.args.get('exclude_tagged', 'false').lower() == 'true'

    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if granularity == 'day':
        fmt = '%Y-%m-%d'
    elif granularity == 'week':
        fmt = '%Y-%W'
    else:
        fmt = '%Y-%m'

    exclude_clause = ""
    if exclude_tagged:
        exclude_clause = """ AND id NOT IN (
            SELECT tt.transaction_id FROM transaction_tags tt
            JOIN tags tg ON tt.tag_id = tg.id WHERE tg.name = '排除统计'
        )"""

    c.execute(f'''SELECT strftime('{fmt}', trans_date) as period,
                         type, SUM(amount), COUNT(*)
                  FROM transactions
                  WHERE is_deleted = 0 AND strftime('%Y', trans_date) = ? {exclude_clause}
                  GROUP BY period, type
                  ORDER BY period''', (str(year),))
    rows = c.fetchall()

    # 累计趋势
    c.execute(f'''SELECT strftime('{fmt}', trans_date) as period,
                         SUM(CASE WHEN type='收入' THEN amount ELSE 0 END),
                         SUM(CASE WHEN type='支出' THEN amount ELSE 0 END)
                  FROM transactions
                  WHERE is_deleted = 0 AND strftime('%Y', trans_date) = ? {exclude_clause}
                  GROUP BY period
                  ORDER BY period''', (str(year),))
    cumulative = c.fetchall()
    conn.close()

    items = [{'period': r[0], 'type': r[1], 'amount': r[2], 'count': r[3]} for r in rows]
    cum_items = [{'period': r[0], 'income': r[1], 'expense': r[2]} for r in cumulative]

    return api_success({
        'granularity': granularity,
        'year': year,
        'items': items,
        'cumulative': cum_items,
    })


# ════════════════════════════════════════════════════════
# 类别/账户/成员 API (增强)
# ════════════════════════════════════════════════════════

@app.route('/api/categories', methods=['GET'])
def get_categories():
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT category, subcategory, COUNT(*), SUM(amount)
                 FROM transactions WHERE is_deleted = 0
                 GROUP BY category, subcategory ORDER BY category, SUM(amount) DESC''')
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


@app.route('/api/categories/quick', methods=['GET'])
def get_quick_categories():
    """获取最常用的子类别（按使用次数排序）"""
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    hidden_cat = _get_hidden('category')
    hidden_sub = _get_hidden('subcategory')
    where = "WHERE is_deleted = 0 AND subcategory != '' AND subcategory IS NOT NULL"
    params = []
    if hidden_cat:
        ph = ','.join(['?'] * len(hidden_cat))
        where += f" AND category NOT IN ({ph})"
        params.extend(hidden_cat)
    if hidden_sub:
        ph = ','.join(['?'] * len(hidden_sub))
        where += f" AND subcategory NOT IN ({ph})"
        params.extend(hidden_sub)
    c.execute(f'''SELECT category, subcategory, COUNT(*) as cnt
                 FROM transactions {where}
                 GROUP BY category, subcategory
                 ORDER BY cnt DESC
                 LIMIT 20''', params)
    rows = c.fetchall()
    conn.close()
    return api_success([{'category': r[0], 'subcategory': r[1], 'count': r[2]} for r in rows])


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


@app.route('/api/projects', methods=['GET'])
def get_projects():
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT project, COUNT(*), SUM(amount)
                 FROM transactions WHERE is_deleted = 0 AND project != ''
                 GROUP BY project ORDER BY COUNT(*) DESC''')
    rows = c.fetchall()
    conn.close()
    return api_success([{'name': r[0], 'count': r[1], 'amount': r[2]} for r in rows])


@app.route('/api/merchants', methods=['GET'])
def get_merchants():
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT merchant, COUNT(*), SUM(amount)
                 FROM transactions WHERE is_deleted = 0 AND merchant != ''
                 GROUP BY merchant ORDER BY COUNT(*) DESC''')
    rows = c.fetchall()
    conn.close()
    return api_success([{'name': r[0], 'count': r[1], 'amount': r[2]} for r in rows])


# ════════════════════════════════════════════════════════
# 预算 API
# ════════════════════════════════════════════════════════

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
            'id': budget_id, 'category': category,
            'year': byear, 'month': bmonth,
            'amount': amount, 'spent': spent,
            'remaining': amount - spent,
            'dimension_type': dim_type, 'dimension_value': dim_value,
        })
    return api_success(items)


@app.route('/api/budgets', methods=['POST'])
@require_json
def set_budget(data):
    sync_db_path()
    category = data.get('category', '')
    amount = data.get('amount')
    if not category or amount is None:
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
            'id': bid, 'category': category,
            'budget': amount, 'spent': spent,
            'remaining': amount - spent,
            'percentage': round(spent / amount * 100, 1) if amount > 0 else 0,
        })
    return api_success(items)


# ════════════════════════════════════════════════════════
# 导出 API
# ════════════════════════════════════════════════════════

@app.route('/api/export', methods=['GET'])
def export_data():
    sync_db_path()
    format_type = request.args.get('format', 'json')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if format_type not in ('json', 'csv'):
        return api_error('不支持的导出格式')
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


# ════════════════════════════════════════════════════════
# 分析 API
# ════════════════════════════════════════════════════════

@app.route('/api/analyze', methods=['GET'])
def analyze():
    sync_db_path()
    tx_module.DB_PATH = DB_PATH
    result = tx_module.analyze_data()
    return api_success({'report': result})


# ════════════════════════════════════════════════════════
# 隐藏项管理 API
# ════════════════════════════════════════════════════════

def _get_hidden(field):
    """获取某个字段的隐藏值列表"""
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM meta WHERE key = ?", (f'hidden_{field}',))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            pass
    return []


def _set_hidden(field, items):
    """设置某个字段的隐藏值列表"""
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
              (f'hidden_{field}', json.dumps(items, ensure_ascii=False)))
    conn.commit()
    conn.close()


@app.route('/api/hidden/<field>', methods=['GET'])
def get_hidden_items(field):
    """获取隐藏项列表"""
    if field not in ('category', 'account', 'merchant', 'member', 'project', 'subcategory'):
        return api_error('不支持的字段')
    items = _get_hidden(field)
    return api_success(items)


@app.route('/api/hidden/<field>', methods=['POST'])
def set_hidden_item(field):
    """隐藏一个值"""
    if field not in ('category', 'account', 'merchant', 'member', 'project', 'subcategory'):
        return api_error('不支持的字段')
    data = request.get_json(silent=True) or {}
    value = data.get('value', '').strip()
    if not value:
        return api_error('值不能为空')
    items = _get_hidden(field)
    if value not in items:
        items.append(value)
        _set_hidden(field, items)
    return api_success(items)


@app.route('/api/hidden/<field>', methods=['DELETE'])
def unhide_item(field):
    """取消隐藏"""
    if field not in ('category', 'account', 'merchant', 'member', 'project', 'subcategory'):
        return api_error('不支持的字段')
    data = request.get_json(silent=True) or {}
    value = data.get('value', '').strip()
    items = _get_hidden(field)
    if value in items:
        items.remove(value)
        _set_hidden(field, items)
    return api_success(items)


# ════════════════════════════════════════════════════════
# 数据库信息 API
# ════════════════════════════════════════════════════════

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
    # 标签数
    c.execute("SELECT COUNT(*) FROM tags")
    tag_count = c.fetchone()[0]
    conn.close()
    return api_success({
        'total_records': total, 'active_records': active,
        'date_range': {'oldest': oldest, 'newest': newest},
        'tag_count': tag_count,
        'db_path': DB_PATH,
    })


# ════════════════════════════════════════════════════════
# 智能导入 API
# ════════════════════════════════════════════════════════

@app.route('/api/import/preview', methods=['POST'])
def import_preview():
    """上传 CSV，返回映射建议 + 预览数据"""
    sync_db_path()
    import_engine.DB_PATH = DB_PATH

    if 'file' not in request.files:
        return api_error('请上传 CSV 文件')

    file = request.files['file']
    if not file.filename:
        return api_error('文件名为空')

    if not file.filename.lower().endswith('.csv'):
        return api_error('只支持 CSV 文件')

    file_bytes = file.read()

    # 限制文件大小 (10MB)
    if len(file_bytes) > 10 * 1024 * 1024:
        return api_error('文件过大，最大支持 10MB')

    # 用户提供的映射（可选）
    user_mapping = None
    mapping_str = request.form.get('mapping')
    if mapping_str:
        try:
            user_mapping = json.loads(mapping_str)
        except Exception:
            pass

    result = import_engine.preview_import(
        file_bytes,
        user_mapping=user_mapping,
        filename=file.filename
    )

    if 'error' in result:
        return api_error(result['error'])

    return api_success(result)


@app.route('/api/import/execute', methods=['POST'])
def import_execute():
    """确认后执行导入"""
    sync_db_path()
    import_engine.DB_PATH = DB_PATH

    if 'file' not in request.files:
        return api_error('请上传 CSV 文件')

    file = request.files['file']
    if not file.filename:
        return api_error('文件名为空')

    file_bytes = file.read()

    # 限制文件大小
    if len(file_bytes) > 10 * 1024 * 1024:
        return api_error('文件过大，最大支持 10MB')

    # 获取映射
    mapping_str = request.form.get('mapping', '{}')
    try:
        mapping = json.loads(mapping_str)
    except Exception:
        return api_error('映射参数格式错误')

    if not mapping:
        return api_error('请提供列映射')

    # 获取标签
    tags_str = request.form.get('tags', '[]')
    try:
        tags = json.loads(tags_str)
    except Exception:
        tags = []

    # 是否跳过重复
    skip_duplicates = request.form.get('skip_duplicates', 'true').lower() == 'true'

    # 数据来源
    batch_source = request.form.get('source')

    result = import_engine.execute_import(
        file_bytes=file_bytes,
        mapping=mapping,
        tags=tags,
        skip_duplicates=skip_duplicates,
        filename=file.filename,
        batch_source=batch_source
    )

    if 'error' in result:
        return api_error(result['error'])

    return api_success(result, message=f"导入完成: {result['imported']} 条")


@app.route('/api/import/batches', methods=['GET'])
def get_import_batches():
    """获取导入批次列表"""
    sync_db_path()
    conn = db_module.sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, source, filename, row_count, mapping, tags, created_at
                 FROM import_batches ORDER BY created_at DESC''')
    rows = c.fetchall()
    conn.close()

    batches = []
    for r in rows:
        batches.append({
            'id': r[0], 'source': r[1], 'filename': r[2],
            'row_count': r[3], 'mapping': r[4], 'tags': r[5],
            'created_at': r[6],
        })

    return api_success(batches)


# ════════════════════════════════════════════════════════
# 增强导出 API
# ════════════════════════════════════════════════════════

@app.route('/api/export/preview', methods=['GET'])
def export_preview():
    """获取导出预览（记录数、日期范围）"""
    sync_db_path()
    export_engine.DB_PATH = DB_PATH

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    account = request.args.get('account')
    type_ = request.args.get('type')
    tag_ids_str = request.args.get('tag_ids')
    tag_ids = None
    if tag_ids_str:
        try:
            tag_ids = [int(x) for x in tag_ids_str.split(',')]
        except Exception:
            pass

    result = export_engine.get_export_preview(
        start_date=start_date, end_date=end_date,
        category=category, account=account,
        type_=type_, tag_ids=tag_ids
    )
    return api_success(result)


@app.route('/api/export/v2', methods=['GET'])
def export_v2():
    """增强导出（支持 Excel/PDF/CSV/JSON）"""
    sync_db_path()
    export_engine.DB_PATH = DB_PATH

    format_type = request.args.get('format', 'excel')
    if format_type not in ('excel', 'csv', 'pdf', 'json'):
        return api_error('不支持的格式，可选: excel, csv, pdf, json')

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    account = request.args.get('account')
    type_ = request.args.get('type')
    tag_ids_str = request.args.get('tag_ids')
    tag_ids = None
    if tag_ids_str:
        try:
            tag_ids = [int(x) for x in tag_ids_str.split(',')]
        except Exception:
            pass

    # Sheet 选项
    sheets_str = request.args.get('sheets', '明细,月度汇总,分类统计,账户统计')
    sheets = [s.strip() for s in sheets_str.split(',')]

    # 获取数据
    data = export_engine.get_export_data(
        start_date=start_date, end_date=end_date,
        category=category, account=account,
        type_=type_, tag_ids=tag_ids
    )

    if data['count'] == 0:
        return api_error('没有数据可导出')

    # 生成临时文件
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    format_map = {
        'excel': ('xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        'csv': ('csv', 'text/csv'),
        'json': ('json', 'application/json'),
        'pdf': ('pdf', 'application/pdf'),
    }

    ext, mime = format_map[format_type]
    filename = f'ledger_export_{timestamp}.{ext}'
    output_path = os.path.join(tmp_dir, filename)

    try:
        if format_type == 'excel':
            export_engine.export_excel(data, output_path, sheets=sheets)
        elif format_type == 'csv':
            import_compatible = request.args.get('import_compatible', 'true').lower() == 'true'
            export_engine.export_csv(data, output_path, import_compatible=import_compatible)
        elif format_type == 'json':
            export_engine.export_json(data, output_path)
        elif format_type == 'pdf':
            title = request.args.get('title', '收支报告')
            export_engine.export_pdf(data, output_path, title=title)
    except Exception as e:
        return api_error(f'导出失败: {str(e)}')

    from flask import send_file
    return send_file(
        output_path,
        mimetype=mime,
        as_attachment=True,
        download_name=filename
    )


# ─── 启动 ──────────────────────────────────────────

if __name__ == '__main__':
    in_docker = os.path.exists('/.dockerenv')
    msg = (
        "\n" + "=" * 50 + "\n"
        + " Ledger Web Service v2\n"
        + "=" * 50 + "\n"
        + "  Database: {}\n".format(DB_PATH)
        + "  Address:  http://{}:{}\n".format(WEB_HOST, WEB_PORT)
        + ("  Mode:     Docker\n" if in_docker else "  Mode:     Native\n")
        + "  Press Ctrl+C to stop\n"
        + "=" * 50 + "\n"
    )
    print(msg, flush=True)
    app.run(host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG)
