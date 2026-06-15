#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse

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

DB_PATH = os.environ.get('LEDGER_DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ledger.db'))


def _sync_db_path():
    db_module.DB_PATH = DB_PATH
    transactions_module.DB_PATH = DB_PATH
    budgets_module.DB_PATH = DB_PATH


def init_db():
    _sync_db_path()
    module_init_db()


def add_transaction(type_, amount, category, subcategory, account, project, member, merchant, note, trans_date=None):
    _sync_db_path()
    module_add_transaction(type_, amount, category, subcategory, account, project, member, merchant, note, trans_date)


def list_transactions(limit=20, include_deleted=False):
    _sync_db_path()
    module_list_transactions(limit, include_deleted)


def summary(year=None, month=None):
    _sync_db_path()
    module_summary(year, month)


def update_transaction(tid, field, value):
    _sync_db_path()
    module_update_transaction(tid, field, value)


def soft_delete_transaction(tid):
    _sync_db_path()
    module_soft_delete_transaction(tid)


def restore_transaction(tid):
    _sync_db_path()
    module_restore_transaction(tid)


def hard_delete_transaction(tid, confirm=False):
    _sync_db_path()
    module_hard_delete_transaction(tid, confirm)


def set_budget(category, amount, year=None, month=None, dimension_type='category', dimension_value=None):
    _sync_db_path()
    module_set_budget(category, amount, year, month, dimension_type, dimension_value)


def check_budget(year=None, month=None):
    _sync_db_path()
    module_check_budget(year, month)


def create_budget_template(name, description='', category=None, amount=0.0, dimension_type='category', dimension_value=None,
                           account=None, project=None, member=None, merchant=None, note=None, year=None, month=None):
    _sync_db_path()
    return module_create_budget_template(name, description, category, amount, dimension_type, dimension_value,
                                         account, project, member, merchant, note, year, month)


def list_budget_templates():
    _sync_db_path()
    return module_list_budget_templates()


def update_budget_template(template_id, **kwargs):
    _sync_db_path()
    return module_update_budget_template(template_id, **kwargs)


def delete_budget_template(template_id):
    _sync_db_path()
    return module_delete_budget_template(template_id)


def apply_budget_template(template_id, year=None, month=None):
    _sync_db_path()
    return module_apply_budget_template(template_id, year, month)


def suggest_budget_templates(limit=3):
    _sync_db_path()
    return module_suggest_budget_templates(limit)


def import_csv(csv_file):
    _sync_db_path()
    return module_import_csv(csv_file)


def reconcile_guide():
    _sync_db_path()
    module_reconcile_guide()


def search_transactions(keyword, search_type='all', limit=50):
    _sync_db_path()
    module_search_transactions(keyword, search_type, limit)


def filter_transactions(category=None, account=None, member=None, merchant=None, project=None, start_date=None, end_date=None, limit=50):
    _sync_db_path()
    module_filter_transactions(category, account, member, merchant, project, start_date, end_date, limit)


def export_transactions(output_file, format_type='csv', category=None, start_date=None, end_date=None):
    _sync_db_path()
    return module_export_transactions(output_file, format_type, category, start_date, end_date)


def get_statistics(year=None, month=None, group_by='category'):
    _sync_db_path()
    module_get_statistics(year, month, group_by)


def list_accounts():
    _sync_db_path()
    module_list_accounts()


def list_categories():
    _sync_db_path()
    module_list_categories()


def list_members():
    _sync_db_path()
    module_list_members()


def main():
    parser = argparse.ArgumentParser(description='记账 API')
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
        if not args.type or args.amount is None:
            print('❌ add 需要 --type 和 --amount')
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
            print('❌ update 需要 --id, --field, --value')
            return
        update_transaction(args.id, args.field, args.value)
    elif args.action == 'delete':
        if not args.id:
            print('❌ delete 需要 --id')
            return
        soft_delete_transaction(args.id)
    elif args.action == 'restore':
        if not args.id:
            print('❌ restore 需要 --id')
            return
        restore_transaction(args.id)
    elif args.action == 'hard_delete':
        if not args.id:
            print('❌ hard_delete 需要 --id')
            return
        hard_delete_transaction(args.id, args.confirm)
    elif args.action == 'budget_set':
        if not args.category or args.amount is None:
            print('❌ budget_set 需要 --category 和 --amount')
            return
        set_budget(args.category, args.amount, args.year, args.month, args.dimension_type, args.dimension_value)
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
        print(f'✅ 已创建模板 ID={template_id}')
    elif args.action == 'budget_template_list':
        for item in list_budget_templates():
            print(f"{item['id']}: {item['name']} | {item['category']} | {item['amount']:.2f} | {item['dimension_type']}:{item['dimension_value'] or '-'}")
    elif args.action == 'budget_template_update':
        if not args.template_id:
            print('❌ budget_template_update 需要 --template_id')
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
        print('✅ 已更新模板' if success else '❌ 未找到模板')
    elif args.action == 'budget_template_delete':
        if not args.template_id:
            print('❌ budget_template_delete 需要 --template_id')
            return
        success = delete_budget_template(args.template_id)
        print('✅ 已删除模板' if success else '❌ 未找到模板')
    elif args.action == 'budget_template_apply':
        if not args.template_id:
            print('❌ budget_template_apply 需要 --template_id')
            return
        apply_budget_template(args.template_id, args.year, args.month)
    elif args.action == 'budget_template_suggest':
        for item in suggest_budget_templates(args.template_limit):
            print(f"建议: {item['name']} | 类目={item['category']} | 金额={item['amount']:.2f} | 维度={item['dimension_type']}:{item['dimension_value']}")
    elif args.action == 'import_csv':
        if not args.file:
            print('❌ import_csv 需要 --file')
            return
        import_csv(args.file)
    elif args.action == 'reconcile_guide':
        reconcile_guide()
    elif args.action == 'search':
        if not args.keyword:
            print('❌ search 需要 --keyword')
            return
        search_transactions(args.keyword, args.search_type, args.limit)
    elif args.action == 'filter':
        filter_transactions(args.category, args.account, args.member, args.merchant,
                           args.project, args.start_date, args.end_date, args.limit)
    elif args.action == 'export':
        if not args.output:
            print('❌ export 需要 --output')
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


if __name__ == '__main__':
    main()
