#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
picoclaw 调用入口 - 统一接口脚本
用法: python3 ledger_cli.py <command> [options]

所有命令都会自动处理路径问题，适用于飞牛NAS环境。
"""

import os
import sys
import subprocess
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SCRIPT_DIR)  # ledger-skills 目录
os.environ['PYTHONUTF8'] = '1'


def load_env_file(env_path):
    """加载 .env 文件"""
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass


def get_ledger_root():
    """获取 ledger 服务目录"""
    # 1. 先加载 Skills 目录下的 .env 文件
    skills_env = os.path.join(SKILLS_DIR, '.env')
    load_env_file(skills_env)
    
    # 2. 检查系统环境变量
    ledger_path = os.environ.get('LEDGER_PATH', '').strip()
    if ledger_path and os.path.isdir(ledger_path):
        return ledger_path
    
    # 3. 尝试常见部署路径
    common_paths = [
        '/volume1/docker/ledger',
        os.path.expanduser('~/ledger'),
        os.path.expanduser('~/docker/ledger'),
    ]
    for path in common_paths:
        if os.path.isdir(path):
            return path
    
    # 4. 最后尝试相对路径推导
    return os.path.dirname(SKILLS_DIR)

def run_ledger_api(action, **kwargs):
    """调用 scripts/cli.py"""
    ledger_root = get_ledger_root()
    cli_path = os.path.join(ledger_root, 'scripts', 'cli.py')
    if not os.path.exists(cli_path):
        return '', f'找不到 cli.py: {cli_path}', 1
    cmd = [sys.executable, cli_path, action]

    for key, value in kwargs.items():
        if value is not None and value is not False and value != '':
            cmd.append(f'--{key}')
            if value is not True:
                cmd.append(str(value))

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.stdout, result.stderr, result.returncode


def format_output(stdout, stderr, returncode):
    """格式化输出为JSON"""
    return json.dumps({
        'success': returncode == 0,
        'data': stdout.strip() if stdout else None,
        'error': stderr.strip() if stderr else None,
    }, ensure_ascii=False, indent=2)


def cmd_add(args):
    kwargs = {
        'type': args.get('type'),
        'amount': args.get('amount'),
        'category': args.get('category'),
        'subcategory': args.get('subcategory'),
        'account': args.get('account'),
        'project': args.get('project'),
        'member': args.get('member'),
        'merchant': args.get('merchant'),
        'note': args.get('note'),
        'date': args.get('date'),
    }
    stdout, stderr, code = run_ledger_api('add', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_list(args):
    kwargs = {
        'limit': args.get('limit', 20),
        'include_deleted': args.get('include_deleted', False),
    }
    stdout, stderr, code = run_ledger_api('list', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_search(args):
    kwargs = {
        'keyword': args.get('keyword'),
        'search_type': args.get('search_type', 'all'),
        'limit': args.get('limit', 50),
    }
    stdout, stderr, code = run_ledger_api('search', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_filter(args):
    kwargs = {
        'category': args.get('category'),
        'account': args.get('account'),
        'member': args.get('member'),
        'merchant': args.get('merchant'),
        'project': args.get('project'),
        'start_date': args.get('start_date'),
        'end_date': args.get('end_date'),
        'limit': args.get('limit', 50),
    }
    stdout, stderr, code = run_ledger_api('filter', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_summary(args):
    kwargs = {'year': args.get('year'), 'month': args.get('month')}
    stdout, stderr, code = run_ledger_api('summary', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_stats(args):
    kwargs = {
        'year': args.get('year'),
        'month': args.get('month'),
        'group_by': args.get('group_by', 'category'),
    }
    stdout, stderr, code = run_ledger_api('stats', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_update(args):
    kwargs = {'id': args.get('id'), 'field': args.get('field'), 'value': args.get('value')}
    stdout, stderr, code = run_ledger_api('update', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_delete(args):
    stdout, stderr, code = run_ledger_api('delete', id=args.get('id'))
    return format_output(stdout, stderr, code)


def cmd_restore(args):
    stdout, stderr, code = run_ledger_api('restore', id=args.get('id'))
    return format_output(stdout, stderr, code)


def cmd_budget_set(args):
    kwargs = {
        'category': args.get('category'),
        'amount': args.get('amount'),
        'year': args.get('year'),
        'month': args.get('month'),
        'dimension_type': args.get('dimension_type'),
        'dimension_value': args.get('dimension_value'),
    }
    stdout, stderr, code = run_ledger_api('budget_set', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_budget_check(args):
    kwargs = {'year': args.get('year'), 'month': args.get('month')}
    stdout, stderr, code = run_ledger_api('budget_check', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_budget_template_create(args):
    kwargs = {
        'template_name': args.get('name'),
        'template_description': args.get('description'),
        'category': args.get('category'),
        'template_amount': args.get('amount'),
        'dimension_type': args.get('dimension_type'),
        'dimension_value': args.get('dimension_value'),
        'account': args.get('account'),
        'project': args.get('project'),
        'member': args.get('member'),
        'merchant': args.get('merchant'),
        'note': args.get('note'),
        'year': args.get('year'),
        'month': args.get('month'),
    }
    stdout, stderr, code = run_ledger_api('budget_template_create', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_budget_template_list(args):
    stdout, stderr, code = run_ledger_api('budget_template_list')
    return format_output(stdout, stderr, code)


def cmd_budget_template_update(args):
    kwargs = {
        'template_id': args.get('id'),
        'template_name': args.get('name'),
        'template_description': args.get('description'),
        'category': args.get('category'),
        'template_amount': args.get('amount'),
        'dimension_type': args.get('dimension_type'),
        'dimension_value': args.get('dimension_value'),
        'account': args.get('account'),
        'project': args.get('project'),
        'member': args.get('member'),
        'merchant': args.get('merchant'),
        'note': args.get('note'),
        'year': args.get('year'),
        'month': args.get('month'),
    }
    stdout, stderr, code = run_ledger_api('budget_template_update', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_budget_template_delete(args):
    stdout, stderr, code = run_ledger_api('budget_template_delete', template_id=args.get('id'))
    return format_output(stdout, stderr, code)


def cmd_budget_template_apply(args):
    stdout, stderr, code = run_ledger_api('budget_template_apply', template_id=args.get('id'), year=args.get('year'), month=args.get('month'))
    return format_output(stdout, stderr, code)


def cmd_budget_template_suggest(args):
    kwargs = {'template_limit': args.get('limit', 3)}
    stdout, stderr, code = run_ledger_api('budget_template_suggest', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_export(args):
    kwargs = {
        'output': args.get('output'),
        'format': args.get('format', 'csv'),
        'category': args.get('category'),
        'start_date': args.get('start_date'),
        'end_date': args.get('end_date'),
    }
    stdout, stderr, code = run_ledger_api('export', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_accounts(args):
    stdout, stderr, code = run_ledger_api('accounts')
    return format_output(stdout, stderr, code)


def cmd_categories(args):
    stdout, stderr, code = run_ledger_api('categories')
    return format_output(stdout, stderr, code)


def cmd_members(args):
    stdout, stderr, code = run_ledger_api('members')
    return format_output(stdout, stderr, code)


def cmd_import(args):
    kwargs = {'file': args.get('file')}
    stdout, stderr, code = run_ledger_api('import_csv', **kwargs)
    return format_output(stdout, stderr, code)


def cmd_reconcile(args):
    stdout, stderr, code = run_ledger_api('reconcile_guide')
    return format_output(stdout, stderr, code)


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
    'export': cmd_export,
    'accounts': cmd_accounts,
    'categories': cmd_categories,
    'members': cmd_members,
    'import': cmd_import,
    'reconcile': cmd_reconcile,
}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': '缺少命令参数', 'available_commands': list(COMMANDS.keys())}, ensure_ascii=False, indent=2))
        sys.exit(1)

    command = sys.argv[1]
    if command not in COMMANDS:
        print(json.dumps({'success': False, 'error': f'未知命令: {command}', 'available_commands': list(COMMANDS.keys())}, ensure_ascii=False, indent=2))
        sys.exit(1)

    args = {}
    if len(sys.argv) > 2:
        try:
            args = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print(json.dumps({'success': False, 'error': '参数必须是JSON格式'}, ensure_ascii=False, indent=2))
            sys.exit(1)

    result = COMMANDS[command](args)
    print(result)


if __name__ == '__main__':
    main()
