#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger CLI - 命令行入口
所有业务逻辑委托给 ledger_modules/ 处理，本文件仅负责参数解析和分发。
"""

import os
import sys
import argparse
from datetime import datetime

# 强制 UTF-8 输出（修复 Windows 编码问题）
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ['PYTHONUTF8'] = '1'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module
from ledger_modules.config import get_db_path

# ── 数据库路径（从配置文件获取）──
DB_PATH = get_db_path()


def _sync_db_path():
    """确保所有模块使用同一数据库路径"""
    db_module.DB_PATH = DB_PATH
    tx_module.DB_PATH = DB_PATH
    budget_module.DB_PATH = DB_PATH


# ── 命令处理函数 ────────────────────────────────────


def cmd_init(args):
    _sync_db_path()
    db_module.init_db()


def cmd_add(args):
    if not args.type or args.amount is None:
        print("❌ add 需要 --type 和 --amount")
        return
    _sync_db_path()
    tx_module.add_transaction(
        args.type, args.amount, args.category, args.subcategory,
        args.account, args.project, args.member, args.merchant,
        args.note, args.date, args.confirm,
    )


def cmd_list(args):
    _sync_db_path()
    tx_module.list_transactions(args.limit, args.include_deleted)


def cmd_summary(args):
    _sync_db_path()
    tx_module.summary(args.year, args.month)


def cmd_update(args):
    if not args.id or not args.field or args.value is None:
        print("❌ update 需要 --id, --field, --value")
        return
    _sync_db_path()
    tx_module.update_transaction(args.id, args.field, args.value)


def cmd_delete(args):
    if not args.id:
        print("❌ delete 需要 --id")
        return
    _sync_db_path()
    tx_module.soft_delete_transaction(args.id)


def cmd_restore(args):
    if not args.id:
        print("❌ restore 需要 --id")
        return
    _sync_db_path()
    tx_module.restore_transaction(args.id)


def cmd_hard_delete(args):
    if not args.id:
        print("❌ hard_delete 需要 --id")
        return
    _sync_db_path()
    tx_module.hard_delete_transaction(args.id, args.confirm)


def cmd_budget_set(args):
    if not args.category or args.amount is None:
        print("❌ budget_set 需要 --category 和 --amount")
        return
    _sync_db_path()
    budget_module.set_budget(
        args.category, args.amount, args.year, args.month,
        args.dimension_type, args.dimension_value,
    )


def cmd_budget_check(args):
    _sync_db_path()
    budget_module.check_budget(args.year, args.month)


def cmd_budget_template_create(args):
    _sync_db_path()
    template_id = budget_module.create_budget_template(
        args.template_name or "未命名模板",
        args.template_description or "",
        args.category,
        args.template_amount or 0.0,
        args.dimension_type or "category",
        args.dimension_value,
        args.account, args.project, args.member, args.merchant,
        args.note, args.year, args.month,
    )
    print(f"✅ 已创建模板 ID={template_id}")


def cmd_budget_template_list(args):
    _sync_db_path()
    for item in budget_module.list_budget_templates():
        print(
            f"{item['id']}: {item['name']} | {item['category']} | "
            f"{item['amount']:.2f} | {item['dimension_type']}:{item['dimension_value'] or '-'}"
        )


def cmd_budget_template_update(args):
    if not args.template_id:
        print("❌ budget_template_update 需要 --template_id")
        return
    _sync_db_path()
    kwargs = {}
    for k in ["template_name", "template_description", "category", "template_amount",
              "dimension_type", "dimension_value", "account", "project",
              "member", "merchant", "note", "year", "month"]:
        v = getattr(args, k, None)
        if v is not None:
            key = k.replace("template_", "")
            key = "amount" if key == "amount" and k == "template_amount" else key
            key = "description" if key == "description" else key
            kwargs[key] = v
    # Fix key names
    field_map = {
        "template_name": "name",
        "template_description": "description",
        "template_amount": "amount",
    }
    resolved = {}
    for k, v in kwargs.items():
        resolved[field_map.get(k, k)] = v

    success = budget_module.update_budget_template(args.template_id, **resolved)
    print("✅ 已更新模板" if success else "❌ 未找到模板")


def cmd_budget_template_delete(args):
    if not args.template_id:
        print("❌ budget_template_delete 需要 --template_id")
        return
    _sync_db_path()
    success = budget_module.delete_budget_template(args.template_id)
    print("✅ 已删除模板" if success else "❌ 未找到模板")


def cmd_budget_template_apply(args):
    if not args.template_id:
        print("❌ budget_template_apply 需要 --template_id")
        return
    _sync_db_path()
    budget_module.apply_budget_template(args.template_id, args.year, args.month)


def cmd_budget_template_suggest(args):
    _sync_db_path()
    for item in budget_module.suggest_budget_templates(args.template_limit):
        print(
            f"建议: {item['name']} | 类目={item['category']} | "
            f"金额={item['amount']:.2f} | 维度={item['dimension_type']}:{item['dimension_value']}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 通用记录模板命令
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_template_create(args):
    if not args.template_name:
        print("❌ template_create 需要 --template_name")
        return
    _sync_db_path()
    template_id = budget_module.create_record_template(
        args.template_name,
        args.template_type or '通用',
        args.type,
        args.template_amount or 0.0,
        args.category,
        args.subcategory,
        args.account,
        args.project,
        args.member,
        args.merchant,
        args.note,
        args.template_description or '',
    )
    print(f"✅ 已创建模板 ID={template_id}")


def cmd_template_list(args):
    _sync_db_path()
    templates = budget_module.list_record_templates(args.template_type)
    if not templates:
        print("暂无模板")
        return
    for item in templates:
        type_str = f" | 类型={item['type']}" if item['type'] else ""
        amount_str = f" | 金额={item['amount']:.2f}" if item['amount'] else ""
        usage_str = f" | 已用{item['usage_count']}次" if item['usage_count'] else ""
        print(f"{item['id']}: {item['name']} | {item['template_type']}{type_str}{amount_str}{usage_str}")


def cmd_template_update(args):
    if not args.template_id:
        print("❌ template_update 需要 --template_id")
        return
    _sync_db_path()
    kwargs = {}
    field_map = {
        "template_name": "name",
        "template_description": "description",
        "template_type": "template_type",
        "type": "type",
        "template_amount": "amount",
        "category": "category",
        "subcategory": "subcategory",
        "account": "account",
        "project": "project",
        "member": "member",
        "merchant": "merchant",
        "note": "note",
    }
    for k, v in field_map.items():
        val = getattr(args, k, None)
        if val is not None:
            kwargs[v] = val
    
    success = budget_module.update_record_template(args.template_id, **kwargs)
    print("✅ 已更新模板" if success else "❌ 未找到模板")


def cmd_template_delete(args):
    if not args.template_id:
        print("❌ template_delete 需要 --template_id")
        return
    _sync_db_path()
    success = budget_module.delete_record_template(args.template_id)
    print("✅ 已删除模板" if success else "❌ 未找到模板")


def cmd_template_apply(args):
    if not args.template_id:
        print("❌ template_apply 需要 --template_id")
        return
    _sync_db_path()
    template = budget_module.apply_record_template(args.template_id, args.template_amount)
    if not template:
        print("❌ 未找到模板")
        return
    
    # 输出模板信息，供调用方使用
    print(f"📋 模板 '{template['name']}' 已加载:")
    print(f"  类型: {template['template_type']}")
    if template['type']:
        print(f"  交易类型: {template['type']}")
    if template['amount']:
        print(f"  金额: {template['amount']:.2f}")
    if template['category']:
        print(f"  类别: {template['category']}")
    if template['account']:
        print(f"  账户: {template['account']}")
    if template['member']:
        print(f"  成员: {template['member']}")
    if template['merchant']:
        print(f"  商家: {template['merchant']}")
    if template['note']:
        print(f"  备注: {template['note']}")


def cmd_template_suggest(args):
    _sync_db_path()
    for item in budget_module.suggest_record_templates(args.template_limit):
        type_str = f" | 类型={item['type']}" if item['type'] else ""
        amount_str = f" | 均额={item['amount']:.2f}" if item['amount'] else ""
        print(f"建议: {item['name']} | {item['template_type']}{type_str}{amount_str}")


def cmd_import_csv(args):
    if not args.file:
        print("❌ import_csv 需要 --file")
        return
    _sync_db_path()
    tx_module.import_csv(args.file)


def cmd_reconcile(args):
    tx_module.reconcile_guide()


def cmd_search(args):
    if not args.keyword:
        print("❌ search 需要 --keyword")
        return
    _sync_db_path()
    tx_module.search_transactions(args.keyword, args.search_type, args.limit)


def cmd_filter(args):
    _sync_db_path()
    tx_module.filter_transactions(
        args.category, args.account, args.member, args.merchant,
        args.project, args.start_date, args.end_date, args.limit,
    )


def cmd_export(args):
    if not args.output:
        print("❌ export 需要 --output")
        return
    _sync_db_path()
    if args.format in ('excel', 'pdf'):
        from ledger_modules import export_engine
        export_engine.DB_PATH = tx_module.DB_PATH
        data = export_engine.get_export_data(
            start_date=args.start_date, end_date=args.end_date,
            category=args.category
        )
        if data['count'] == 0:
            print("没有数据可导出")
            return
        if args.format == 'excel':
            export_engine.export_excel(data, args.output)
        else:
            export_engine.export_pdf(data, args.output)
        print(f"✅ 已导出 {data['count']} 条记录到 {args.output}")
    else:
        tx_module.export_transactions(args.output, args.format, args.category, args.start_date, args.end_date)


def cmd_stats(args):
    _sync_db_path()
    tx_module.get_statistics(args.year, args.month, args.group_by)


def cmd_accounts(args):
    _sync_db_path()
    tx_module.list_accounts()


def cmd_categories(args):
    _sync_db_path()
    tx_module.list_categories()


def cmd_members(args):
    _sync_db_path()
    tx_module.list_members()


def cmd_analyze(args):
    """分析用户数据，输出结构化摘要供 agent 学习"""
    _sync_db_path()
    tx_module.analyze_data()


# ── 主入口 ─────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="📒 Ledger - 个人记账系统")
    parser.add_argument("action", choices=[
        "init",
        "add", "list", "summary", "update", "delete", "restore", "hard_delete",
        "budget_set", "budget_check",
        "budget_template_create", "budget_template_list",
        "budget_template_update", "budget_template_delete", "budget_template_apply",
        "budget_template_suggest",
        "template_create", "template_list", "template_update", "template_delete",
        "template_apply", "template_suggest",
        "import_csv", "reconcile_guide",
        "search", "filter", "export", "stats",
        "accounts", "categories", "members", "analyze",
    ])

    # ── 交易参数 ──
    parser.add_argument("--type", choices=["支出", "收入"])
    parser.add_argument("--amount", type=float)
    parser.add_argument("--category")
    parser.add_argument("--subcategory")
    parser.add_argument("--account")
    parser.add_argument("--project")
    parser.add_argument("--member")
    parser.add_argument("--merchant")
    parser.add_argument("--note")
    parser.add_argument("--date")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--id", type=int)
    parser.add_argument("--field")
    parser.add_argument("--value")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--include_deleted", action="store_true")

    # ── 搜索/筛选/导出 ──
    parser.add_argument("--keyword")
    parser.add_argument("--search_type", choices=["all", "note", "category", "merchant"], default="all")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["csv", "json", "excel", "pdf"], default="csv")
    parser.add_argument("--start_date")
    parser.add_argument("--end_date")
    parser.add_argument("--group_by", choices=["category", "account", "month"], default="category")
    parser.add_argument("--file")

    # ── 预算/模板参数 ──
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--dimension_type", choices=["category", "account", "member", "project", "merchant"])
    parser.add_argument("--dimension_value")
    parser.add_argument("--template_id", type=int)
    parser.add_argument("--template_name")
    parser.add_argument("--template_description")
    parser.add_argument("--template_amount", type=float)
    parser.add_argument("--template_type")
    parser.add_argument("--template_limit", type=int, default=3)

    args = parser.parse_args()

    # 自动初始化（所有操作前确保表存在）
    _sync_db_path()
    if args.action != "init":
        db_module.init_db()

    # 路由
    dispatch = {
        "init": cmd_init,
        "add": cmd_add,
        "list": cmd_list,
        "summary": cmd_summary,
        "update": cmd_update,
        "delete": cmd_delete,
        "restore": cmd_restore,
        "hard_delete": cmd_hard_delete,
        "budget_set": cmd_budget_set,
        "budget_check": cmd_budget_check,
        "budget_template_create": cmd_budget_template_create,
        "budget_template_list": cmd_budget_template_list,
        "budget_template_update": cmd_budget_template_update,
        "budget_template_delete": cmd_budget_template_delete,
        "budget_template_apply": cmd_budget_template_apply,
        "budget_template_suggest": cmd_budget_template_suggest,
        "template_create": cmd_template_create,
        "template_list": cmd_template_list,
        "template_update": cmd_template_update,
        "template_delete": cmd_template_delete,
        "template_apply": cmd_template_apply,
        "template_suggest": cmd_template_suggest,
        "import_csv": cmd_import_csv,
        "reconcile_guide": cmd_reconcile,
        "search": cmd_search,
        "filter": cmd_filter,
        "export": cmd_export,
        "stats": cmd_stats,
        "accounts": cmd_accounts,
        "categories": cmd_categories,
        "members": cmd_members,
        "analyze": cmd_analyze,
    }
    dispatch[args.action](args)


if __name__ == "__main__":
    main()
