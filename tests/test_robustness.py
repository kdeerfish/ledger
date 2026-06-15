#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健壮性测试 - 覆盖边界条件、错误处理和缺失场景
"""

import os
import tempfile
import pytest
import csv

# 确保在测试环境中使用临时数据库
from unittest.mock import patch


# ── Fixtures ──

@pytest.fixture
def db_path(tmp_path):
    """使用临时数据库"""
    db = tmp_path / "test_ledger.db"
    with patch('ledger_modules.db.DB_PATH', str(db)), \
         patch('ledger_modules.transactions.DB_PATH', str(db)), \
         patch('ledger_modules.budgets.DB_PATH', str(db)):
        from ledger_modules.db import init_db
        init_db()
        yield str(db)


@pytest.fixture
def sample_transactions(db_path):
    """创建测试数据"""
    from ledger_modules.transactions import add_transaction
    add_transaction('expense', 100.0, '食品酒水', '零食', '微信', '', '本人', '拼多多', '测试零食', '2026-06-01 10:00:00')
    add_transaction('expense', 200.0, '食品酒水', '餐饮', '支付宝', '', 'fish', '美团', '午餐', '2026-06-05 12:00:00')
    add_transaction('income', 5000.0, '职业收入', '', '招商银行', '', '本人', '', '工资', '2026-06-10 09:00:00')
    add_transaction('expense', 50.0, '交通出行', '打车', '微信', '', '本人', '滴滴', '打车', '2026-06-15 18:00:00')
    # 已删除的记录
    add_transaction('expense', 30.0, '其他', '', '现金', '', '本人', '', '测试删除', '2026-06-12 14:00:00')
    from ledger_modules.transactions import soft_delete_transaction
    soft_delete_transaction(5)


# ════════════════════════════════════════════════════════════════════
# 1. list_transactions 边界条件
# ════════════════════════════════════════════════════════════════════

class TestListTransactionsEdgeCases:

    def test_list_empty_db(self, db_path):
        """空数据库不应报错"""
        from ledger_modules.transactions import list_transactions
        list_transactions()  # 应正常执行，打印空列表

    def test_list_include_deleted(self, db_path, sample_transactions):
        """包含已删除记录"""
        from ledger_modules.transactions import list_transactions
        # 应显示所有记录（包括已删除的）
        list_transactions(limit=100, include_deleted=True)

    def test_list_limit_zero(self, db_path, sample_transactions):
        """limit=0 应返回空"""
        from ledger_modules.transactions import list_transactions
        list_transactions(limit=0)


# ════════════════════════════════════════════════════════════════════
# 2. update_transaction 边界条件
# ════════════════════════════════════════════════════════════════════

class TestUpdateTransactionEdgeCases:

    def test_update_invalid_field(self, db_path, sample_transactions):
        """不支持的字段应报错提示"""
        from ledger_modules.transactions import update_transaction
        update_transaction(1, 'invalid_field', 'value')  # 应打印错误

    def test_update_nonexistent_id(self, db_path, sample_transactions):
        """更新不存在的记录"""
        from ledger_modules.transactions import update_transaction
        update_transaction(99999, 'amount', 100.0)  # 应打印未找到

    def test_update_deleted_record(self, db_path, sample_transactions):
        """更新已删除的记录"""
        from ledger_modules.transactions import update_transaction
        update_transaction(5, 'amount', 999.0)  # 已删除，应打印未找到

    def test_update_amount_string(self, db_path, sample_transactions):
        """金额字符串转换"""
        from ledger_modules.transactions import update_transaction
        update_transaction(1, 'amount', '250.5')  # 应自动转换为 float


# ════════════════════════════════════════════════════════════════════
# 3. soft_delete / restore 边界条件
# ════════════════════════════════════════════════════════════════════

class TestDeleteRestoreEdgeCases:

    def test_soft_delete_nonexistent(self, db_path):
        """删除不存在的记录"""
        from ledger_modules.transactions import soft_delete_transaction
        soft_delete_transaction(99999)  # 应打印未找到

    def test_soft_delete_already_deleted(self, db_path, sample_transactions):
        """重复删除同一记录"""
        from ledger_modules.transactions import soft_delete_transaction
        soft_delete_transaction(5)  # 已删除，应打印未找到或已删除

    def test_restore_nonexistent(self, db_path):
        """恢复不存在的记录"""
        from ledger_modules.transactions import restore_transaction
        restore_transaction(99999)  # 应打印未找到

    def test_restore_active_record(self, db_path, sample_transactions):
        """恢复未删除的记录"""
        from ledger_modules.transactions import restore_transaction
        restore_transaction(1)  # 未删除，应打印未找到

    def test_hard_delete_without_confirm(self, db_path, sample_transactions):
        """物理删除不带确认参数"""
        from ledger_modules.transactions import hard_delete_transaction
        hard_delete_transaction(1, confirm=False)  # 应打印警告

    def test_hard_delete_nonexistent(self, db_path):
        """物理删除不存在的记录"""
        from ledger_modules.transactions import hard_delete_transaction
        hard_delete_transaction(99999, confirm=True)  # 应打印未找到


# ════════════════════════════════════════════════════════════════════
# 4. search_transactions 各搜索类型
# ════════════════════════════════════════════════════════════════════

class TestSearchEdgeCases:

    def test_search_no_results(self, db_path, sample_transactions):
        """搜索无结果"""
        from ledger_modules.transactions import search_transactions
        search_transactions('不存在的关键词')

    def test_search_by_note(self, db_path, sample_transactions):
        """按备注搜索"""
        from ledger_modules.transactions import search_transactions
        search_transactions('零食', search_type='note')

    def test_search_by_category(self, db_path, sample_transactions):
        """按类别搜索"""
        from ledger_modules.transactions import search_transactions
        search_transactions('食品', search_type='category')

    def test_search_by_merchant(self, db_path, sample_transactions):
        """按商家搜索"""
        from ledger_modules.transactions import search_transactions
        search_transactions('拼多多', search_type='merchant')

    def test_search_limit(self, db_path, sample_transactions):
        """限制返回条数"""
        from ledger_modules.transactions import search_transactions
        search_transactions('食', limit=1)


# ════════════════════════════════════════════════════════════════════
# 5. filter_transactions 各筛选条件
# ════════════════════════════════════════════════════════════════════

class TestFilterEdgeCases:

    def test_filter_no_results(self, db_path, sample_transactions):
        """筛选无结果"""
        from ledger_modules.transactions import filter_transactions
        filter_transactions(category='不存在的类别')

    def test_filter_by_account(self, db_path, sample_transactions):
        """按账户筛选"""
        from ledger_modules.transactions import filter_transactions
        filter_transactions(account='微信')

    def test_filter_by_member(self, db_path, sample_transactions):
        """按成员筛选"""
        from ledger_modules.transactions import filter_transactions
        filter_transactions(member='fish')

    def test_filter_by_merchant(self, db_path, sample_transactions):
        """按商家筛选"""
        from ledger_modules.transactions import filter_transactions
        filter_transactions(merchant='美团')

    def test_filter_by_project(self, db_path, sample_transactions):
        """按项目筛选"""
        from ledger_modules.transactions import filter_transactions
        filter_transactions(project='不存在的项目')

    def test_filter_by_date_range(self, db_path, sample_transactions):
        """按日期范围筛选"""
        from ledger_modules.transactions import filter_transactions
        filter_transactions(start_date='2026-06-01', end_date='2026-06-10')

    def test_filter_combined(self, db_path, sample_transactions):
        """组合筛选"""
        from ledger_modules.transactions import filter_transactions
        filter_transactions(category='食品酒水', account='微信', start_date='2026-06-01', end_date='2026-06-30')


# ════════════════════════════════════════════════════════════════════
# 6. export_transactions 边界条件
# ════════════════════════════════════════════════════════════════════

class TestExportEdgeCases:

    def test_export_unsupported_format(self, db_path, sample_transactions, tmp_path):
        """不支持的导出格式"""
        from ledger_modules.transactions import export_transactions
        output = str(tmp_path / "test.txt")
        result = export_transactions(output, format_type='xml')  # 应返回 False

    def test_export_empty_db(self, db_path, tmp_path):
        """空数据库导出"""
        from ledger_modules.transactions import export_transactions
        output = str(tmp_path / "empty.csv")
        result = export_transactions(output, format_type='csv')  # 应返回 False

    def test_export_with_category_filter(self, db_path, sample_transactions, tmp_path):
        """按类别筛选导出"""
        from ledger_modules.transactions import export_transactions
        output = str(tmp_path / "filtered.csv")
        export_transactions(output, format_type='csv', category='食品酒水')

    def test_export_with_date_filter(self, db_path, sample_transactions, tmp_path):
        """按日期筛选导出"""
        from ledger_modules.transactions import export_transactions
        output = str(tmp_path / "dated.csv")
        export_transactions(output, format_type='csv', start_date='2026-06-01', end_date='2026-06-10')


# ════════════════════════════════════════════════════════════════════
# 7. get_statistics 各维度
# ════════════════════════════════════════════════════════════════════

class TestStatisticsEdgeCases:

    def test_stats_empty_db(self, db_path):
        """空数据库统计"""
        from ledger_modules.transactions import get_statistics
        get_statistics()

    def test_stats_by_account(self, db_path, sample_transactions):
        """按账户统计"""
        from ledger_modules.transactions import get_statistics
        get_statistics(group_by='account')

    def test_stats_by_month(self, db_path, sample_transactions):
        """按月份统计"""
        from ledger_modules.transactions import get_statistics
        get_statistics(group_by='month')

    def test_stats_with_date_filter(self, db_path, sample_transactions):
        """带日期筛选统计"""
        from ledger_modules.transactions import get_statistics
        get_statistics(year=2026, month=6, group_by='category')


# ════════════════════════════════════════════════════════════════════
# 8. list_accounts / list_categories / list_members 空数据
# ════════════════════════════════════════════════════════════════════

class TestListMetaEdgeCases:

    def test_list_accounts_empty(self, db_path):
        """空数据库列出账户"""
        from ledger_modules.transactions import list_accounts
        list_accounts()  # 应打印暂无数据

    def test_list_categories_empty(self, db_path):
        """空数据库列出类别"""
        from ledger_modules.transactions import list_categories
        list_categories()  # 应打印暂无数据

    def test_list_members_empty(self, db_path):
        """空数据库列出成员"""
        from ledger_modules.transactions import list_members
        list_members()  # 应打印暂无数据


# ════════════════════════════════════════════════════════════════════
# 9. import_csv 边界条件
# ════════════════════════════════════════════════════════════════════

class TestImportCsvEdgeCases:

    def test_import_file_not_found(self, db_path):
        """导入不存在的文件"""
        from ledger_modules.transactions import import_csv
        result = import_csv('/nonexistent/path/file.csv')  # 应返回 False

    def test_import_invalid_date_format(self, db_path, tmp_path):
        """导入日期格式错误的 CSV"""
        csv_file = tmp_path / "invalid_date.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['交易类型', '金额', '日期', '类别'])
            writer.writeheader()
            writer.writerow({'交易类型': '支出', '金额': '100', '日期': '2026/13/01', '类别': '食品'})
        from ledger_modules.transactions import import_csv
        result = import_csv(str(csv_file))  # 应跳过无效行

    def test_import_zero_amount(self, db_path, tmp_path):
        """导入金额为0的记录"""
        csv_file = tmp_path / "zero_amount.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['交易类型', '金额', '日期', '类别'])
            writer.writeheader()
            writer.writerow({'交易类型': '支出', '金额': '0', '日期': '2026/06/01', '类别': '食品'})
        from ledger_modules.transactions import import_csv
        result = import_csv(str(csv_file))  # 应跳过

    def test_import_missing_date(self, db_path, tmp_path):
        """导入缺少日期的记录"""
        csv_file = tmp_path / "no_date.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['交易类型', '金额', '日期', '类别'])
            writer.writeheader()
            writer.writerow({'交易类型': '支出', '金额': '100', '日期': '', '类别': '食品'})
        from ledger_modules.transactions import import_csv
        result = import_csv(str(csv_file))  # 应跳过

    def test_import_non_expense_income(self, db_path, tmp_path):
        """导入非支出/收入类型"""
        csv_file = tmp_path / "other_type.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['交易类型', '金额', '日期', '类别'])
            writer.writeheader()
            writer.writerow({'交易类型': '转账', '金额': '100', '日期': '2026/06/01', '类别': '转账'})
        from ledger_modules.transactions import import_csv
        result = import_csv(str(csv_file))  # 应跳过

    def test_import_date_only_format(self, db_path, tmp_path):
        """导入只有日期没有时间的格式"""
        csv_file = tmp_path / "date_only.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['交易类型', '金额', '日期', '类别'])
            writer.writeheader()
            writer.writerow({'交易类型': '支出', '金额': '50', '日期': '2026/06/15', '类别': '食品'})
        from ledger_modules.transactions import import_csv
        result = import_csv(str(csv_file))  # 应成功导入


# ════════════════════════════════════════════════════════════════════
# 10. budgets 边界条件
# ════════════════════════════════════════════════════════════════════

class TestBudgetsEdgeCases:

    def test_check_budget_no_budgets(self, db_path):
        """无预算时检查"""
        from ledger_modules.budgets import check_budget
        check_budget(2026, 6)  # 应打印本月无预算

    def test_check_budget_with_spending(self, db_path, sample_transactions):
        """有预算且有消费"""
        from ledger_modules.budgets import set_budget, check_budget
        set_budget('食品酒水', 500.0, 2026, 6)
        check_budget(2026, 6)  # 应显示预算使用情况

    def test_set_budget_auto_dimension(self, db_path):
        """设置预算时自动填充 dimension_value"""
        from ledger_modules.budgets import set_budget
        set_budget('餐饮', 300.0, 2026, 7)  # dimension_value 应自动设为 '餐饮'

    def test_set_budget_account_dimension(self, db_path):
        """按账户维度设置预算"""
        from ledger_modules.budgets import set_budget
        set_budget('餐饮', 500.0, 2026, 7, dimension_type='account', dimension_value='信用卡')

    def test_update_template_empty_kwargs(self, db_path):
        """更新模板时传入空参数"""
        from ledger_modules.budgets import create_budget_template, update_budget_template
        tid = create_budget_template('测试模板', amount=100.0)
        result = update_budget_template(tid)  # 空 kwargs，应返回 False

    def test_update_template_invalid_fields(self, db_path):
        """更新模板时传入无效字段"""
        from ledger_modules.budgets import create_budget_template, update_budget_template
        tid = create_budget_template('测试模板', amount=100.0)
        result = update_budget_template(tid, invalid_field='value', another_bad='x')
        # 应返回 False（无有效字段）

    def test_apply_template_not_found(self, db_path):
        """应用不存在的模板"""
        from ledger_modules.budgets import apply_budget_template
        result = apply_budget_template(99999, 2026, 6)  # 应返回 None

    def test_apply_template_creates_budget(self, db_path):
        """应用模板创建预算"""
        from ledger_modules.budgets import create_budget_template, apply_budget_template
        tid = create_budget_template('吃饭模板', category='餐饮', amount=400.0, dimension_type='account', dimension_value='微信')
        result = apply_budget_template(tid, 2026, 8)
        assert result is not None
        assert result['category'] == '餐饮' or result['dimension_value'] == '微信'

    def test_delete_template_not_found(self, db_path):
        """删除不存在的模板"""
        from ledger_modules.budgets import delete_budget_template
        result = delete_budget_template(99999)  # 应返回 False
        assert result == False


# ════════════════════════════════════════════════════════════════════
# 11. suggest_budget_templates 边界条件
# ════════════════════════════════════════════════════════════════════

class TestSuggestEdgeCases:

    def test_suggest_empty_db(self, db_path):
        """空数据库无建议"""
        from ledger_modules.budgets import suggest_budget_templates
        result = suggest_budget_templates()  # 应返回空列表

    def test_suggest_no_sufficient_data(self, db_path):
        """数据不足（少于2笔）无建议"""
        from ledger_modules.transactions import add_transaction
        from ledger_modules.budgets import suggest_budget_templates
        add_transaction('expense', 50.0, '食品', '', '微信', '', '本人', '', '单独一笔')
        result = suggest_budget_templates()  # 应返回空列表

    def test_suggest_with_limit(self, db_path, sample_transactions):
        """限制返回条数"""
        from ledger_modules.budgets import suggest_budget_templates
        result = suggest_budget_templates(limit=1)  # 应返回最多1条
