#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新增功能测试 - 去重检查、中文类型、通用模板、schema
"""

import os
import sys
import json
import tempfile
import sqlite3
from datetime import datetime

import pytest

import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module


class TestDuplicateCheck:
    """去重检查测试"""

    def test_no_duplicate(self, temp_db):
        """无重复记录时返回空列表"""
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 10:00:00")
        # 使用不同日期检查，应该没有重复
        duplicates = tx_module.check_duplicate("支出", 100.0, "食品", "微信", "2026-06-16 10:00:00")
        assert len(duplicates) == 0

    def test_duplicate_found(self, temp_db):
        """存在重复记录时返回相似记录"""
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 10:00:00")
        duplicates = tx_module.check_duplicate("支出", 100.0, "食品", "微信", "2026-06-15 15:00:00")
        assert len(duplicates) == 1
        assert duplicates[0]['amount'] == 100.0
        assert duplicates[0]['category'] == "食品"

    def test_add_with_duplicate_warning(self, temp_db):
        """添加重复记录时返回 None"""
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 10:00:00")
        result = tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 15:00:00")
        assert result is None

    def test_add_with_force(self, temp_db):
        """使用 force 参数可以强制添加重复记录"""
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 10:00:00")
        result = tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 15:00:00", force=True)
        assert result is not None
        # 验证有两条记录
        rows = self._fetch(temp_db)
        assert len(rows) == 2

    def test_different_amount_no_duplicate(self, temp_db):
        """不同金额不算重复"""
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 10:00:00")
        duplicates = tx_module.check_duplicate("支出", 200.0, "食品", "微信", "2026-06-15 10:00:00")
        assert len(duplicates) == 0

    def test_different_category_no_duplicate(self, temp_db):
        """不同类别不算重复"""
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 10:00:00")
        duplicates = tx_module.check_duplicate("支出", 100.0, "交通", "微信", "2026-06-15 10:00:00")
        assert len(duplicates) == 0

    @staticmethod
    def _fetch(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM transactions")
        rows = c.fetchall()
        conn.close()
        return rows


class TestChineseType:
    """中文类型测试"""

    def test_add_expense_chinese(self, temp_db):
        """添加中文类型支出"""
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "", "测试", "2026-06-15 10:00:00")
        rows = self._fetch(temp_db)
        assert rows[0][1] == "支出"

    def test_add_income_chinese(self, temp_db):
        """添加中文类型收入"""
        tx_module.add_transaction("收入", 5000.0, "工资", "", "银行", "", "本人", "", "测试", "2026-06-15 10:00:00")
        rows = self._fetch(temp_db)
        assert rows[0][1] == "收入"

    def test_summary_chinese_type(self, temp_db):
        """汇总统计使用中文类型"""
        tx_module.add_transaction("支出", 100.0, "食品", "", "微信", "", "本人", "", "", "2026-06-15 10:00:00")
        tx_module.add_transaction("收入", 5000.0, "工资", "", "银行", "", "本人", "", "", "2026-06-15 10:00:00")
        # 验证数据库中的类型是中文
        rows = self._fetch(temp_db)
        types = {row[1] for row in rows}
        assert "支出" in types
        assert "收入" in types

    @staticmethod
    def _fetch(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM transactions")
        rows = c.fetchall()
        conn.close()
        return rows


class TestRecordTemplate:
    """通用记录模板测试"""

    def test_create_template(self, temp_db):
        """创建模板"""
        template_id = budget_module.create_record_template(
            name="零食模板",
            template_type="支出",
            type_="支出",
            amount=30.0,
            category="食品酒水",
            subcategory="零食",
            account="微信零钱",
            merchant="拼多多"
        )
        assert template_id is not None
        assert template_id > 0

    def test_list_templates(self, temp_db):
        """列出模板"""
        budget_module.create_record_template("模板1", "支出", "支出", 30.0, "食品")
        budget_module.create_record_template("模板2", "收入", "收入", 5000.0, "工资")
        
        # 列出所有模板
        templates = budget_module.list_record_templates()
        assert len(templates) == 2
        
        # 按类型列出
        expense_templates = budget_module.list_record_templates("支出")
        assert len(expense_templates) == 1
        assert expense_templates[0]['name'] == "模板1"

    def test_get_template(self, temp_db):
        """获取单个模板"""
        template_id = budget_module.create_record_template("测试模板", "支出", "支出", 100.0, "食品")
        template = budget_module.get_record_template(template_id)
        assert template is not None
        assert template['name'] == "测试模板"
        assert template['amount'] == 100.0

    def test_update_template(self, temp_db):
        """更新模板"""
        template_id = budget_module.create_record_template("原始模板", "支出", "支出", 100.0, "食品")
        success = budget_module.update_record_template(template_id, name="更新后模板", amount=200.0)
        assert success
        template = budget_module.get_record_template(template_id)
        assert template['name'] == "更新后模板"
        assert template['amount'] == 200.0

    def test_delete_template(self, temp_db):
        """删除模板"""
        template_id = budget_module.create_record_template("要删除的模板", "支出", "支出", 100.0, "食品")
        success = budget_module.delete_record_template(template_id)
        assert success
        template = budget_module.get_record_template(template_id)
        assert template is None

    def test_apply_template(self, temp_db):
        """应用模板"""
        template_id = budget_module.create_record_template(
            "午餐模板", "支出", "支出", 25.0, "餐饮", "午餐", "食堂"
        )
        template = budget_module.apply_record_template(template_id)
        assert template is not None
        assert template['name'] == "午餐模板"
        assert template['amount'] == 25.0
        
        # 验证使用次数增加
        template = budget_module.get_record_template(template_id)
        assert template['usage_count'] == 1
        assert template['last_used_at'] is not None

    def test_apply_template_with_override(self, temp_db):
        """应用模板并覆盖金额"""
        template_id = budget_module.create_record_template(
            "午餐模板", "支出", "支出", 25.0, "餐饮", "午餐", "食堂"
        )
        template = budget_module.apply_record_template(template_id, amount_override=35.0)
        assert template['amount'] == 35.0

    def test_suggest_templates(self, temp_db):
        """推荐模板"""
        # 添加多条相似记录
        for i in range(3):
            tx_module.add_transaction(
                "支出", 30.0 + i, "食品", "零食", "微信", "", "本人", "拼多多", 
                f"测试{i}", f"2026-06-15 {10+i}:00:00", force=True
            )
        
        suggestions = budget_module.suggest_record_templates()
        assert len(suggestions) > 0
        # 应该有食品相关的推荐
        categories = [s['category'] for s in suggestions]
        assert "食品" in categories


class TestSchema:
    """Schema 测试"""

    def test_schema_file_exists(self):
        """schema.json 文件存在"""
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'schema.json')
        assert os.path.exists(schema_path)

    def test_schema_valid_json(self):
        """schema.json 是有效的 JSON"""
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'schema.json')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        assert 'transactions' in schema
        assert 'record_templates' in schema
        assert 'commands' in schema

    def test_schema_has_required_fields(self):
        """schema 包含必要字段定义"""
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'schema.json')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # 检查 transactions 表字段
        tx_fields = schema['transactions']['fields']
        assert 'type' in tx_fields
        assert 'amount' in tx_fields
        assert 'category' in tx_fields
        
        # 检查 type 字段的合法值
        type_values = tx_fields['type']['values']
        assert '收入' in type_values
        assert '支出' in type_values
        
        # 检查 analyze 命令
        assert 'analyze' in schema['commands']
        
        # 检查 field_guide
        assert 'field_guide' in schema


class TestAnalyze:
    """analyze 数据分析测试"""

    def test_analyze_empty_db(self, temp_db):
        """空数据库的分析"""
        result = tx_module.analyze_data()
        assert '总览' in result
        assert '0 笔记录' in result

    def test_analyze_with_data(self, sample_db):
        """有数据的分析"""
        result = tx_module.analyze_data()
        assert '总览' in result
        assert '4128' not in result  # sample_db 只有5条记录
        assert '账户' in result
        assert '商家' in result
        assert '类别' in result
        assert '成员' in result
        assert '字段使用率' in result

    def test_analyze_cross_correlation(self, temp_db):
        """交叉关联分析"""
        # 添加数据
        tx_module.add_transaction("支出", 100.0, "食品", "零食", "微信", "", "本人", "拼多多", "测试", "2026-06-15 10:00:00", force=True)
        tx_module.add_transaction("支出", 50.0, "食品", "零食", "微信", "", "本人", "拼多多", "测试", "2026-06-15 11:00:00", force=True)
        tx_module.add_transaction("支出", 30.0, "交通", "打车", "支付宝", "", "本人", "滴滴", "测试", "2026-06-15 12:00:00", force=True)
        
        result = tx_module.analyze_data()
        assert '拼多多' in result
        assert '微信' in result
        assert '食品' in result

    def test_analyze_returns_string(self, temp_db):
        """analyze 返回字符串"""
        result = tx_module.analyze_data()
        assert isinstance(result, str)
