#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖率提升测试 - 针对尚未覆盖的代码路径
目标：将总覆盖率从 60% 提升到 75%+
"""

import os
import csv
import json
import tempfile
import sqlite3
from unittest.mock import patch

import pytest

import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module
import ledger_modules.db as db_module


# ════════════════════════════════════════════════════════════════════
# 1. transactions.py - list_transactions 完整覆盖
# ════════════════════════════════════════════════════════════════════

class TestListTransactionsFull:
    """list_transactions 函数完整覆盖"""

    def test_list_normal_branch(self, sample_db):
        """正常分支：7列（非删除模式）"""
        tx_module.list_transactions(limit=10, include_deleted=False)

    def test_list_deleted_branch(self, sample_db):
        """已删除分支：8列（包含删除状态）"""
        tx_module.list_transactions(limit=10, include_deleted=True)

    def test_list_no_data(self, temp_db):
        """空数据库"""
        tx_module.list_transactions(limit=10, include_deleted=False)


# ════════════════════════════════════════════════════════════════════
# 2. transactions.py - summary 函数覆盖
# ════════════════════════════════════════════════════════════════════

class TestSummaryFull:
    """summary 函数完整覆盖"""

    def test_summary_all(self, sample_db):
        """汇总所有数据"""
        tx_module.summary()

    def test_summary_by_year(self, sample_db):
        """按年筛选"""
        tx_module.summary(year=2026)

    def test_summary_by_year_month(self, sample_db):
        """按年月筛选"""
        tx_module.summary(year=2026, month=6)

    def test_summary_no_data(self, temp_db):
        """空数据库汇总"""
        tx_module.summary()


# ════════════════════════════════════════════════════════════════════
# 3. transactions.py - search_transactions 各搜索类型
# ════════════════════════════════════════════════════════════════════

class TestSearchFull:
    """search_transactions 完整覆盖"""

    def test_search_all(self, sample_db):
        """搜索全部字段"""
        tx_module.search_transactions('零食', search_type='all')

    def test_search_note(self, sample_db):
        """按备注搜索"""
        tx_module.search_transactions('零食', search_type='note')

    def test_search_category(self, sample_db):
        """按类别搜索"""
        tx_module.search_transactions('食品', search_type='category')

    def test_search_merchant(self, sample_db):
        """按商家搜索"""
        tx_module.search_transactions('拼多多', search_type='merchant')

    def test_search_no_result(self, sample_db):
        """搜索无结果"""
        tx_module.search_transactions('完全不存在的关键词')


# ════════════════════════════════════════════════════════════════════
# 4. transactions.py - filter_transactions 完整覆盖
# ════════════════════════════════════════════════════════════════════

class TestFilterFull:
    """filter_transactions 完整覆盖"""

    def test_filter_all_params(self, sample_db):
        """所有筛选参数"""
        tx_module.filter_transactions(
            category='食品', account='微信', member='本人',
            merchant='拼多多', project='项目A',
            start_date='2026-06-01', end_date='2026-06-30', limit=10
        )

    def test_filter_no_results(self, sample_db):
        """筛选无结果"""
        tx_module.filter_transactions(category='不存在的类别')

    def test_filter_empty(self, temp_db):
        """空数据库筛选"""
        tx_module.filter_transactions()


# ════════════════════════════════════════════════════════════════════
# 5. transactions.py - export_transactions 带筛选
# ════════════════════════════════════════════════════════════════════

class TestExportFull:
    """export_transactions 完整覆盖"""

    def test_export_csv_with_filters(self, sample_db, tmp_path):
        """带筛选导出 CSV"""
        output = str(tmp_path / "filtered.csv")
        tx_module.export_transactions(
            output, 'csv', category='食品',
            start_date='2026-06-01', end_date='2026-06-30'
        )

    def test_export_json_with_filters(self, sample_db, tmp_path):
        """带筛选导出 JSON"""
        output = str(tmp_path / "filtered.json")
        tx_module.export_transactions(
            output, 'json', category='食品'
        )

    def test_export_unsupported_format(self, sample_db, tmp_path):
        """不支持的导出格式"""
        output = str(tmp_path / "output.xml")
        result = tx_module.export_transactions(output, 'xml')
        assert result is False


# ════════════════════════════════════════════════════════════════════
# 6. transactions.py - get_statistics 各维度
# ════════════════════════════════════════════════════════════════════

class TestStatisticsFull:
    """get_statistics 完整覆盖"""

    def test_stats_by_category(self, sample_db):
        """按类别统计"""
        tx_module.get_statistics(group_by='category')

    def test_stats_by_account(self, sample_db):
        """按账户统计"""
        tx_module.get_statistics(group_by='account')

    def test_stats_by_month(self, sample_db):
        """按月份统计"""
        tx_module.get_statistics(group_by='month')

    def test_stats_with_year_month(self, sample_db):
        """带年月筛选"""
        tx_module.get_statistics(year=2026, month=6, group_by='category')

    def test_stats_empty(self, temp_db):
        """空数据库统计"""
        tx_module.get_statistics()


# ════════════════════════════════════════════════════════════════════
# 7. transactions.py - list_accounts/categories/members 有数据
# ════════════════════════════════════════════════════════════════════

class TestListMetaFull:
    """list_accounts/categories/members 完整覆盖"""

    def test_list_accounts_with_data(self, sample_db):
        """列出账户（有数据）"""
        tx_module.list_accounts()

    def test_list_categories_with_data(self, sample_db):
        """列出类别（有数据）"""
        tx_module.list_categories()

    def test_list_members_with_data(self, sample_db):
        """列出成员（有数据）"""
        tx_module.list_members()


# ════════════════════════════════════════════════════════════════════
# 8. transactions.py - reconcile_guide
# ════════════════════════════════════════════════════════════════════

class TestReconcileGuide:
    """reconcile_guide 函数覆盖"""

    def test_reconcile_guide(self):
        """对账指南应正常输出"""
        tx_module.reconcile_guide()


# ════════════════════════════════════════════════════════════════════
# 9. transactions.py - import_csv 完整覆盖
# ════════════════════════════════════════════════════════════════════

class TestImportCsvFull:
    """import_csv 完整覆盖"""

    def test_import_valid_full(self, temp_db, tmp_path):
        """导入有效 CSV（含所有字段）"""
        csv_file = tmp_path / "full.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                '交易类型', '金额', '日期', '类别', '子类别',
                '账户', '项目', '成员', '商家', '备注'
            ])
            writer.writeheader()
            writer.writerow({
                '交易类型': '支出', '金额': '100.5', '日期': '2026/06/15 10:30',
                '类别': '食品', '子类别': '零食', '账户': '微信',
                '项目': '项目A', '成员': '本人', '商家': '拼多多', '备注': '测试'
            })
            writer.writerow({
                '交易类型': '收入', '金额': '5000', '日期': '2026/06/10',
                '类别': '工资', '子类别': '', '账户': '银行',
                '项目': '', '成员': '本人', '商家': '', '备注': '月工资'
            })
            # 跳过类型
            writer.writerow({
                '交易类型': '转账', '金额': '100', '日期': '2026/06/01',
                '类别': '转账', '子类别': '', '账户': '银行',
                '项目': '', '成员': '本人', '商家': '', '备注': '跳过'
            })
            # 金额为 0
            writer.writerow({
                '交易类型': '支出', '金额': '0', '日期': '2026/06/01',
                '类别': '测试', '子类别': '', '账户': '',
                '项目': '', '成员': '', '商家': '', '备注': '跳过'
            })
            # 日期为空
            writer.writerow({
                '交易类型': '支出', '金额': '50', '日期': '',
                '类别': '测试', '子类别': '', '账户': '',
                '项目': '', '成员': '', '商家': '', '备注': '跳过'
            })
        result = tx_module.import_csv(str(csv_file))
        assert result is True

    def test_import_invalid_date_all_formats(self, temp_db, tmp_path):
        """导入日期格式全错"""
        csv_file = tmp_path / "bad_date.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['交易类型', '金额', '日期', '类别'])
            writer.writeheader()
            writer.writerow({'交易类型': '支出', '金额': '100', '日期': '2026-06-15', '类别': '食品'})
        result = tx_module.import_csv(str(csv_file))
        assert result is True

    def test_import_missing_file(self, temp_db):
        """导入不存在文件"""
        result = tx_module.import_csv('/nonexistent/path/file.csv')
        assert result is False


# ════════════════════════════════════════════════════════════════════
# 10. budgets.py - set_budget 默认年月
# ════════════════════════════════════════════════════════════════════

class TestBudgetsFull:
    """budgets 模块完整覆盖"""

    def test_set_budget_default_date(self, temp_db):
        """设置预算时不传年月"""
        budget_module.set_budget('餐饮', 500.0)

    def test_set_budget_replace(self, temp_db):
        """设置预算覆盖已有预算"""
        budget_module.set_budget('餐饮', 500.0, 2026, 6)
        budget_module.set_budget('餐饮', 600.0, 2026, 6)

    def test_check_budget_with_data(self, sample_db):
        """有数据时检查预算"""
        budget_module.set_budget('食品', 1000.0, 2026, 6)
        budget_module.set_budget('交通', 200.0, 2026, 6)
        budget_module.check_budget(2026, 6)

    def test_create_template_full(self, temp_db):
        """创建模板（含所有字段）"""
        tid = budget_module.create_budget_template(
            name='完整模板', description='测试模板',
            dimension_type='account', dimension_value='微信',
            amount=500.0, category='餐饮',
            account='微信', project='项目A', member='本人',
            merchant='美团', note='测试', year=2026, month=6
        )
        assert tid is not None and tid > 0

    def test_list_templates_with_data(self, temp_db):
        """列出模板（有数据）"""
        budget_module.create_budget_template('模板1', amount=100.0)
        budget_module.create_budget_template('模板2', amount=200.0)
        templates = budget_module.list_budget_templates()
        assert len(templates) == 2

    def test_update_template_valid(self, temp_db):
        """更新模板（有效字段）"""
        tid = budget_module.create_budget_template('测试', amount=100.0)
        result = budget_module.update_budget_template(
            tid, name='更新后', amount=300.0, category='交通'
        )
        assert result is True

    def test_apply_template_category_dimension(self, temp_db):
        """应用模板（category 维度，无 dimension_value）"""
        tid = budget_module.create_budget_template(
            '默认模板', category='餐饮', amount=400.0,
            dimension_type='category', dimension_value=None
        )
        result = budget_module.apply_budget_template(tid, 2026, 9)
        assert result is not None
        assert result['category'] == '餐饮'

    def test_suggest_templates_with_data(self, sample_db):
        """有足够数据时建议模板"""
        # sample_db 已有5条记录，部分可聚合
        suggestions = budget_module.suggest_budget_templates(limit=5)
        assert isinstance(suggestions, list)

    def test_suggest_templates_limit(self, sample_db):
        """限制建议数量"""
        suggestions = budget_module.suggest_budget_templates(limit=1)
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 1


# ════════════════════════════════════════════════════════════════════
# 11. db.py - 迁移逻辑覆盖
# ════════════════════════════════════════════════════════════════════

class TestDbMigration:
    """数据库迁移逻辑覆盖"""

    def test_init_with_existing_budgets_no_dimension(self, tmp_path):
        """测试 budgets 表缺少 dimension_type/dimension_value 时的迁移"""
        db_path = str(tmp_path / "migrate_test.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # 创建旧版 budgets 表（无 dimension_type/dimension_value）
        c.execute('''CREATE TABLE budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            year INTEGER,
            month INTEGER,
            amount REAL,
            UNIQUE(category, year, month)
        )''')
        c.execute("INSERT INTO budgets (category, year, month, amount) VALUES ('餐饮', 2026, 6, 500)")
        # 创建旧版 transactions 表（无 is_deleted）
        c.execute('''CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            category TEXT,
            subcategory TEXT,
            account TEXT,
            project TEXT,
            member TEXT,
            merchant TEXT,
            note TEXT,
            trans_date TEXT
        )''')
        conn.commit()
        conn.close()
        # 现在 init_db 应该自动迁移
        with patch.object(db_module, 'DB_PATH', db_path):
            with patch.object(tx_module, 'DB_PATH', db_path):
                with patch.object(budget_module, 'DB_PATH', db_path):
                    db_module.init_db()
        # 验证迁移后数据完整
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("PRAGMA table_info(budgets)")
        cols = {row[1] for row in c.fetchall()}
        assert 'dimension_type' in cols
        assert 'dimension_value' in cols
        c.execute("SELECT category, dimension_type FROM budgets WHERE category='餐饮'")
        row = c.fetchone()
        assert row is not None
        assert row[1] == 'category'
        # 验证 is_deleted 列已添加
        c.execute("PRAGMA table_info(transactions)")
        tx_cols = {row[1] for row in c.fetchall()}
        assert 'is_deleted' in tx_cols
        conn.close()

    def test_init_new_database(self, tmp_path):
        """全新数据库初始化"""
        db_path = str(tmp_path / "new_test.db")
        with patch.object(db_module, 'DB_PATH', db_path):
            db_module.init_db()
        assert os.path.exists(db_path)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in c.fetchall()}
        conn.close()
        assert 'transactions' in tables
        assert 'budgets' in tables
        assert 'budget_templates' in tables
