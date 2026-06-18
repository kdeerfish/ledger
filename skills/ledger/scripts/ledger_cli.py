#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger Agent 调用入口 — HTTP API 版
通过 REST API 访问 Docker 中的 Ledger 服务

用法: python3 ledger_cli.py <command> '<json_args>'

配置优先级：
  1. 环境变量 LEDGER_API_URL
  2. skills/ledger/.env 中的 LEDGER_API_URL
  3. 默认值 http://127.0.0.1:5000
"""

import json
import os
import sys
import urllib.request
import urllib.error

# 强制 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SCRIPT_DIR)
ENV_FILE = os.path.join(SKILLS_DIR, '.env')

# ── API 基础地址 ─────────────────────────────────────

def _load_env_file(path):
    """加载 .env，不覆盖已有环境变量"""
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, _, v = line.partition('=')
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass


def get_api_url():
    """获取 API 基础地址"""
    _load_env_file(ENV_FILE)

    # 1. 环境变量
    url = os.environ.get('LEDGER_API_URL', '').strip()
    if url:
        return url.rstrip('/')

    # 2. 本地回环地址（适合 Agent 和 Web 同机）
    return 'http://127.0.0.1:5000'


# ── HTTP 请求封装 ────────────────────────────────────

def api_get(path, params=None):
    """GET 请求"""
    url = get_api_url() + path
    if params:
        qs = urllib.parse.urlencode(params)
        url += '?' + qs
    req = urllib.request.Request(url, method='GET',
                                 headers={'Accept': 'application/json'})
    return _do_request(req)


def api_post(path, body=None):
    """POST 请求"""
    url = get_api_url() + path
    data = json.dumps(body or {}).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'Accept': 'application/json'})
    return _do_request(req)


def api_put(path, body=None):
    """PUT 请求"""
    url = get_api_url() + path
    data = json.dumps(body or {}).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, method='PUT',
                                 headers={'Content-Type': 'application/json',
                                          'Accept': 'application/json'})
    return _do_request(req)


def api_delete(path):
    """DELETE 请求"""
    url = get_api_url() + path
    req = urllib.request.Request(url, method='DELETE',
                                 headers={'Accept': 'application/json'})
    return _do_request(req)


def _do_request(req):
    """执行请求，统一解析 JSON 响应"""
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode('utf-8'))
            return err
        except Exception:
            return {'success': False, 'error': f'HTTP {e.code}: {e.reason}'}
    except urllib.error.URLError as e:
        return {'success': False, 'error': f'无法连接 API: {e.reason}。请确认 Ledger Docker 容器已启动且 LEDGER_API_URL 配置正确。'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _ensure(data, fields):
    """辅助：组装参数"""
    return {f: data.get(f) for f in fields if data.get(f) is not None and data.get(f) != ''}


# ═══════════════════════════════════════════════════════════════════════════════
# 交易命令
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_add(args):
    return api_post('/api/transactions', {
        'type': args.get('type', '支出'),
        'amount': args.get('amount'),
        'category': args.get('category', ''),
        'subcategory': args.get('subcategory', ''),
        'account': args.get('account', ''),
        'project': args.get('project', ''),
        'member': args.get('member', ''),
        'merchant': args.get('merchant', ''),
        'note': args.get('note', ''),
        'date': args.get('date'),
        'force': args.get('force', False),
    })


def cmd_list(args):
    params = {'limit': args.get('limit', 20)}
    if args.get('include_deleted'):
        params['include_deleted'] = '1'
    result = api_get('/api/transactions', params)
    # 保持向后兼容
    if result.get('success') and result.get('data'):
        txs = result['data'].get('transactions', [])
        total = result['data'].get('total', 0)
        lines = [f"共 {total} 条记录："]
        for t in txs:
            amt = f"¥{t['amount']:.2f}" if t.get('amount') else '¥0.00'
            cat = t.get('category', '-')
            acc = t.get('account', '-')
            note = t.get('note', '')
            d = (t.get('date') or '')[:10]
            lines.append(f"#{t['id']}: {d} | {t['type']} | {amt} | {cat} | {acc} | {note}")
        result['data'] = "\n".join(lines)
    return result


def cmd_search(args):
    params = _ensure(args, ['keyword', 'search_type'])
    params.setdefault('keyword', '')
    params.setdefault('search_type', 'all')
    if args.get('limit'):
        params['limit'] = args['limit']
    result = api_get('/api/transactions/search', params)
    if result.get('success') and isinstance(result.get('data'), list):
        items = result['data']
        lines = [f"找到 {len(items)} 条相关记录："]
        for t in items:
            amt = f"¥{t['amount']:.2f}" if t.get('amount') else '¥0.00'
            lines.append(f"#{t['id']}: {t.get('date','')[:10]} | {t['type']} | {amt} | {t.get('category','-')} | {t.get('account','-')} | {t.get('note','')}")
        result['data'] = "\n".join(lines)
    return result


def cmd_filter(args):
    params = {}
    for f in ['category', 'account', 'member', 'merchant', 'project', 'start_date', 'end_date']:
        v = args.get(f)
        if v:
            params[f] = v
    if args.get('limit'):
        params['limit'] = args['limit']
    # filter 通过 list + filter 实现，我们用 search 的 filter 方式
    # 实际上直接调 GET /api/transactions 加上参数
    result = api_get('/api/transactions', params)
    if result.get('success') and result.get('data'):
        txs = result['data'].get('transactions', [])
        lines = [f"找到 {len(txs)} 条记录："]
        for t in txs:
            amt = f"¥{t['amount']:.2f}" if t.get('amount') else '¥0.00'
            lines.append(f"#{t['id']}: {t.get('date','')[:10]} | {t['type']} | {amt} | {t.get('category','-')} | {t.get('account','-')} | {t.get('note','')}")
        result['data'] = "\n".join(lines)
    return result


def cmd_summary(args):
    params = {}
    for k in ['year', 'month']:
        v = args.get(k)
        if v is not None:
            params[k] = v
    result = api_get('/api/summary', params)
    if result.get('success') and result.get('data'):
        d = result['data']
        period = f"{d.get('year') or '所有'}-{d.get('month') or '全年'}"
        lines = [
            f"收支统计 ({period}):",
            f"  收入: ¥{d['income']:.2f}" if d.get('income') else "  收入: ¥0.00",
            f"  支出: ¥{d['expense']:.2f}" if d.get('expense') else "  支出: ¥0.00",
            f"  结余: ¥{d['balance']:.2f}" if d.get('balance') else "  结余: ¥0.00",
        ]
        result['data'] = "\n".join(lines)
    return result


def cmd_stats(args):
    params = {'group_by': args.get('group_by', 'category')}
    for k in ['year', 'month']:
        v = args.get(k)
        if v is not None:
            params[k] = v
    result = api_get('/api/stats', params)
    if result.get('success') and result.get('data'):
        items = result['data'].get('items', [])
        lines = [f"按{params['group_by']}统计："]
        for i in items:
            lines.append(f"  {i['group']} ({i['type']}): ¥{i['total']:.2f}, {i['count']}笔")
        result['data'] = "\n".join(lines)
    return result


def cmd_update(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    return api_put(f'/api/transactions/{tid}', {
        'field': args.get('field'),
        'value': args.get('value'),
    })


def cmd_delete(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    return api_delete(f'/api/transactions/{tid}')


def cmd_restore(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    return api_post(f'/api/transactions/{tid}/restore')


# ═══════════════════════════════════════════════════════════════════════════════
# 预算命令
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_budget_set(args):
    body = _ensure(args, ['category', 'amount', 'year', 'month', 'dimension_type', 'dimension_value'])
    result = api_post('/api/budgets', body)
    if result.get('success'):
        result['data'] = f"预算已设置: {args.get('category')} {args.get('year') or '今年'}-{args.get('month') or '本月'} 限额 ¥{args.get('amount')}"
    return result


def cmd_budget_check(args):
    params = {}
    for k in ['year', 'month']:
        v = args.get(k)
        if v is not None:
            params[k] = v
    result = api_get('/api/budgets/check', params)
    if result.get('success') and isinstance(result.get('data'), list):
        items = result['data']
        if not items:
            result['data'] = "本月无预算"
        else:
            lines = ["预算检查结果："]
            for b in items:
                pct = b.get('percentage', 0)
                warn = " ⚠️ 超支!" if pct > 100 else " ⚠️ 接近上限" if pct > 80 else ""
                lines.append(f"  {b['category']}: 预算 ¥{b['budget']:.2f}, 已用 ¥{b['spent']:.2f} ({pct}%), 剩余 ¥{b['remaining']:.2f}{warn}")
            result['data'] = "\n".join(lines)
    return result


def cmd_budget_template_create(args):
    return api_post('/api/budgets/templates', _ensure(args, [
        'name', 'description', 'category', 'amount', 'dimension_type',
        'dimension_value', 'account', 'project', 'member', 'merchant', 'note', 'year', 'month',
    ]))


def cmd_budget_template_list(args):
    return api_get('/api/budgets/templates')


def cmd_budget_template_update(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    return api_put(f'/api/budgets/templates/{tid}', _ensure(args, [
        'name', 'description', 'category', 'amount', 'dimension_type',
        'dimension_value', 'account', 'project', 'member', 'merchant', 'note', 'year', 'month',
    ]))


def cmd_budget_template_delete(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    return api_delete(f'/api/budgets/templates/{tid}')


def cmd_budget_template_apply(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    body = {}
    for k in ['year', 'month']:
        v = args.get(k)
        if v is not None:
            body[k] = v
    return api_post(f'/api/budgets/templates/{tid}/apply', body)


def cmd_budget_template_suggest(args):
    params = {'limit': args.get('limit', 3)}
    return api_get('/api/budgets/templates/suggest', params)


# ═══════════════════════════════════════════════════════════════════════════════
# 通用记录模板命令
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_template_create(args):
    return api_post('/api/record_templates', _ensure(args, [
        'name', 'description', 'template_type', 'type', 'amount',
        'category', 'subcategory', 'account', 'project', 'member', 'merchant', 'note',
    ]))


def cmd_template_list(args):
    params = {}
    v = args.get('template_type')
    if v:
        params['template_type'] = v
    return api_get('/api/record_templates', params)


def cmd_template_update(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    return api_put(f'/api/record_templates/{tid}', _ensure(args, [
        'name', 'description', 'template_type', 'type', 'amount',
        'category', 'subcategory', 'account', 'project', 'member', 'merchant', 'note',
    ]))


def cmd_template_delete(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    return api_delete(f'/api/record_templates/{tid}')


def cmd_template_apply(args):
    tid = args.get('id')
    if not tid:
        return {'success': False, 'error': '需要 id'}
    body = {}
    v = args.get('amount')
    if v is not None:
        body['amount'] = v
    return api_post(f'/api/record_templates/{tid}/apply', body)


def cmd_template_suggest(args):
    params = {'limit': args.get('limit', 5)}
    return api_get('/api/record_templates/suggest', params)


# ═══════════════════════════════════════════════════════════════════════════════
# 数据 / 查询命令
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_export(args):
    params = _ensure(args, ['format', 'category', 'start_date', 'end_date'])
    params.setdefault('format', 'json')
    result = api_get('/api/export', params)
    if result.get('success') and result.get('data'):
        d = result['data']
        lines = [f"已导出 {d.get('count', 0)} 条记录"]
        if d.get('data'):
            # 转成 CSV 格式输出来适配原有接口
            records = d['data']
            if params.get('format') == 'csv':
                import csv
                import io
                buf = io.StringIO()
                w = csv.writer(buf)
                w.writerow(['ID', '日期', '类型', '金额', '类别', '子类别', '账户', '项目', '成员', '商家', '备注'])
                for r in records:
                    w.writerow([r['id'], r['date'], r['type'], r['amount'], r['category'],
                                r.get('subcategory',''), r['account'], r.get('project',''),
                                r.get('member',''), r.get('merchant',''), r.get('note','')])
                result['data'] = buf.getvalue()
            else:
                result['data'] = json.dumps(records, ensure_ascii=False, indent=2)
        else:
            result['data'] = "\n".join(lines)
    return result


def cmd_accounts(args):
    result = api_get('/api/accounts')
    if result.get('success') and isinstance(result.get('data'), list):
        items = result['data']
        lines = [f"所有账户 ({len(items)} 个)："]
        for a in items:
            lines.append(f"  - {a['name']} ({a['count']}笔, ¥{a['amount']:.2f})")
        result['data'] = "\n".join(lines)
    return result


def cmd_categories(args):
    result = api_get('/api/categories')
    if result.get('success') and isinstance(result.get('data'), list):
        lines = ["所有类别："]
        for c in result['data']:
            lines.append(f"\n  {c['name']} ({c['total_count']}笔, ¥{c['total_amount']:.2f}):")
            for s in c['subcategories']:
                lines.append(f"    - {s['name']} ({s['count']}笔, ¥{s['amount']:.2f})")
        result['data'] = "\n".join(lines)
    return result


def cmd_members(args):
    result = api_get('/api/members')
    if result.get('success') and isinstance(result.get('data'), list):
        items = result['data']
        lines = [f"所有成员 ({len(items)} 个)："]
        for m in items:
            lines.append(f"  - {m['name']} ({m['count']}笔, ¥{m['amount']:.2f})")
        result['data'] = "\n".join(lines)
    return result


def cmd_analyze(args):
    result = api_get('/api/analyze')
    if result.get('success') and result.get('data'):
        report = result['data'].get('report', '')
        result['data'] = report
    return result


def cmd_health(args):
    """检查 API 连接状态"""
    result = api_get('/api/health')
    if result.get('success') or result.get('status') == 'ok':
        d = result
        return {
            'success': True,
            'data': f"API 连接正常 | 数据库: {d.get('database', '?')} | 记录数: {d.get('records', 0)} | 版本: {d.get('version', '?')}"
        }
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 命令注册
# ═══════════════════════════════════════════════════════════════════════════════

COMMANDS = {
    'add': cmd_add,
    'list': cmd_list,
    'search': cmd_search,
    'filter': cmd_filter,
    'summary': cmd_summary,
    'stats': cmd_stats,
    'update': cmd_update,
    'delete': cmd_delete,
    'restore': cmd_restore,
    'budget_set': cmd_budget_set,
    'budget_check': cmd_budget_check,
    'budget_template_create': cmd_budget_template_create,
    'budget_template_list': cmd_budget_template_list,
    'budget_template_update': cmd_budget_template_update,
    'budget_template_delete': cmd_budget_template_delete,
    'budget_template_apply': cmd_budget_template_apply,
    'budget_template_suggest': cmd_budget_template_suggest,
    'template_create': cmd_template_create,
    'template_list': cmd_template_list,
    'template_update': cmd_template_update,
    'template_delete': cmd_template_delete,
    'template_apply': cmd_template_apply,
    'template_suggest': cmd_template_suggest,
    'export': cmd_export,
    'accounts': cmd_accounts,
    'categories': cmd_categories,
    'members': cmd_members,
    'analyze': cmd_analyze,
    'health': cmd_health,
}


def main():
    if len(sys.argv) < 2:
        info = {'success': False, 'error': '缺少命令参数', 'available_commands': list(COMMANDS.keys())}
        print(json.dumps(info, ensure_ascii=False, indent=2))
        sys.exit(1)

    command = sys.argv[1]
    if command not in COMMANDS:
        info = {'success': False, 'error': f'未知命令: {command}', 'available_commands': list(COMMANDS.keys())}
        print(json.dumps(info, ensure_ascii=False, indent=2))
        sys.exit(1)

    args = {}
    if len(sys.argv) > 2:
        try:
            args = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            info = {'success': False, 'error': '参数必须是JSON格式'}
            print(json.dumps(info, ensure_ascii=False, indent=2))
            sys.exit(1)

    result = COMMANDS[command](args)
    # 确保输出为统一 JSON 格式
    if not isinstance(result, dict):
        result = {'success': True, 'data': str(result)}
    if 'success' not in result:
        result = {'success': True, 'data': result}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
