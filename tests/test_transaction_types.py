#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易类型系统测试
"""

import pytest

import ledger_modules.transaction_types as type_mod


class TestCanonicalTypes:
    def test_type_choices(self):
        assert type_mod.TYPE_CHOICES == [
            type_mod.INCOME,
            type_mod.EXPENSE,
            type_mod.TRANSFER,
            type_mod.BALANCE_ADJUST,
            type_mod.LIABILITY_CHANGE,
            type_mod.CLAIMS_CHANGE,
            type_mod.RECONCILIATION,
        ]

    def test_type_order(self):
        assert type_mod.TYPE_ORDER[0] == type_mod.INCOME
        assert type_mod.TYPE_ORDER[1] == type_mod.EXPENSE
        assert type_mod.TYPE_ORDER[2] == type_mod.TRANSFER


class TestNormalizeRawType:
    @pytest.mark.parametrize("raw,expected", [
        ("收入", "收入"),
        ("支出", "支出"),
        ("转账", "转账"),
        ("转入", "转账"),
        ("转出", "转账"),
        ("还信用卡", "转账"),
        ("代付", "转账"),
        ("余额变更", "余额变更"),
        ("负债变更", "负债变更"),
        ("债权变更", "债权变更"),
        ("调整", "调整"),
        ("", None),
        (None, None),
    ])
    def test_normalize(self, raw, expected):
        assert type_mod.normalize_raw_type(raw) == expected

    def test_income_aliases(self):
        for alias in ["收入", "income", "收款", "卖水收入", "退保", "意外来钱", "房租押金", "报销"]:
            assert type_mod.normalize_raw_type(alias) == type_mod.INCOME

    def test_expense_aliases(self):
        for alias in ["支出", "expense", "消费", "付款", "退款"]:
            assert type_mod.normalize_raw_type(alias) == type_mod.EXPENSE


class TestStatHelpers:
    def test_is_stat_income(self):
        assert type_mod.is_stat_income(type_mod.INCOME)
        assert not type_mod.is_stat_income(type_mod.TRANSFER)
        assert not type_mod.is_stat_income(type_mod.BALANCE_ADJUST)

    def test_is_stat_expense(self):
        assert type_mod.is_stat_expense(type_mod.EXPENSE)
        assert not type_mod.is_stat_expense(type_mod.TRANSFER)
        assert not type_mod.is_stat_expense(type_mod.RECONCILIATION)

    def test_is_transfer(self):
        assert type_mod.is_transfer(type_mod.TRANSFER)
        assert not type_mod.is_transfer(type_mod.INCOME)

    def test_is_balance_sheet(self):
        assert type_mod.is_balance_sheet(type_mod.BALANCE_ADJUST)
        assert type_mod.is_balance_sheet(type_mod.LIABILITY_CHANGE)
        assert type_mod.is_balance_sheet(type_mod.CLAIMS_CHANGE)
        assert not type_mod.is_balance_sheet(type_mod.INCOME)

    def test_is_excluded_from_income_expense(self):
        assert type_mod.is_excluded_from_income_expense(type_mod.TRANSFER)
        assert type_mod.is_excluded_from_income_expense(type_mod.BALANCE_ADJUST)
        assert type_mod.is_excluded_from_income_expense(type_mod.LIABILITY_CHANGE)
        assert type_mod.is_excluded_from_income_expense(type_mod.CLAIMS_CHANGE)
        assert type_mod.is_excluded_from_income_expense(type_mod.RECONCILIATION)
        assert not type_mod.is_excluded_from_income_expense(type_mod.INCOME)
        assert not type_mod.is_excluded_from_income_expense(type_mod.EXPENSE)


class TestLegacyTypeMap:
    def test_legacy_mapping(self):
        assert type_mod.LEGACY_TYPE_MAP["转入"] == type_mod.TRANSFER
        assert type_mod.LEGACY_TYPE_MAP["转出"] == type_mod.TRANSFER
        assert type_mod.LEGACY_TYPE_MAP["余额变更"] == type_mod.BALANCE_ADJUST
        assert type_mod.LEGACY_TYPE_MAP["负债变更"] == type_mod.LIABILITY_CHANGE
        assert type_mod.LEGACY_TYPE_MAP["债权变更"] == type_mod.CLAIMS_CHANGE
