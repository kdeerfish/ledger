#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入引擎测试
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ledger_modules.db as db_module
import ledger_modules.import_engine as import_engine


@pytest.fixture
def engine_db(temp_db):
    """让导入引擎使用临时数据库"""
    import_engine.DB_PATH = temp_db
    return temp_db


# ─── 编码检测 ──────────────────────────────────────────────

class TestDetectEncoding:
    def test_utf8(self):
        data = '日期,金额\n2024-01-01,100'.encode('utf-8')
        assert import_engine.detect_encoding(data) == 'utf-8'

    def test_utf8_bom(self):
        data = b'\xef\xbb\xbf' + '日期,金额\n'.encode('utf-8')
        assert import_engine.detect_encoding(data) == 'utf-8-sig'

    def test_gbk(self):
        data = '日期,金额\n2024-01-01,100'.encode('gbk')
        enc = import_engine.detect_encoding(data)
        # 应该能检测出非 utf-8
        assert enc != 'utf-8'


# ─── 列名推断 ──────────────────────────────────────────────

class TestInferMapping:
    def test_standard_headers(self):
        headers = ['交易类型', '日期', '金额', '类别', '账户', '商家', '备注']
        mapping = import_engine.infer_mapping(headers)
        assert mapping['交易类型']['target'] == 'type'
        assert mapping['日期']['target'] == 'date'
        assert mapping['金额']['target'] == 'amount'
        assert mapping['类别']['target'] == 'category'
        assert mapping['账户']['target'] == 'account'
        assert mapping['商家']['target'] == 'merchant'
        assert mapping['备注']['target'] == 'note'

    def test_alipay_headers(self):
        headers = ['交易创建时间', '交易对方', '商品说明', '收/支', '金额', '收/付款方式']
        mapping = import_engine.infer_mapping(headers)
        assert mapping['交易创建时间']['target'] == 'date'
        assert mapping['交易对方']['target'] == 'merchant'
        assert mapping['商品说明']['target'] == 'note'
        assert mapping['金额']['target'] == 'amount'

    def test_unknown_headers(self):
        headers = ['foo', 'bar', 'baz']
        mapping = import_engine.infer_mapping(headers)
        assert mapping['foo']['target'] is None
        assert mapping['bar']['target'] is None

    def test_conflict_resolution(self):
        # 两个列都可能映射到 amount
        headers = ['金额', '交易金额']
        mapping = import_engine.infer_mapping(headers)
        mapping = import_engine._resolve_mapping_conflicts(mapping)
        # 只有一个应该被映射
        mapped = [h for h, info in mapping.items() if info['target'] == 'amount']
        assert len(mapped) == 1


# ─── 值标准化 ──────────────────────────────────────────────

class TestNormalizeType:
    def test_expense(self):
        assert import_engine.normalize_type('支出') == '支出'
        assert import_engine.normalize_type('消费') == '支出'

    def test_income(self):
        assert import_engine.normalize_type('收入') == '收入'
        assert import_engine.normalize_type('收款') == '收入'

    def test_unknown(self):
        assert import_engine.normalize_type('转账') is None
        assert import_engine.normalize_type('') is None


class TestNormalizeAmount:
    def test_normal(self):
        assert import_engine.normalize_amount('100.50') == 100.50

    def test_with_currency(self):
        assert import_engine.normalize_amount('¥1,234.56') == 1234.56
        assert import_engine.normalize_amount('￥100') == 100.0

    def test_zero(self):
        assert import_engine.normalize_amount('0') is None

    def test_negative(self):
        assert import_engine.normalize_amount('-50') is None

    def test_invalid(self):
        assert import_engine.normalize_amount('abc') is None
        assert import_engine.normalize_amount('') is None


class TestNormalizeDate:
    def test_slash_format(self):
        assert import_engine.normalize_date('2024/06/15 14:30') == '2024-06-15 14:30:00'

    def test_dash_format(self):
        assert import_engine.normalize_date('2024-06-15 14:30:00') == '2024-06-15 14:30:00'

    def test_date_only(self):
        assert import_engine.normalize_date('2024/06/15') == '2024-06-15 00:00:00'

    def test_compact(self):
        assert import_engine.normalize_date('20240615') == '2024-06-15 00:00:00'

    def test_invalid(self):
        assert import_engine.normalize_date('not a date') is None
        assert import_engine.normalize_date('') is None


class TestNormalizeValue:
    def test_exact_match(self):
        result, conf, method = import_engine.normalize_value(
            'account', '招商银行', existing_values=['招商银行', '支付宝']
        )
        assert result == '招商银行'
        assert conf == 1.0

    def test_synonym_match(self):
        synonyms = {'account': {'招商银行': ['招行', '招商']}}
        result, conf, method = import_engine.normalize_value(
            'account', '招行',
            existing_values=['招商银行', '支付宝'],
            synonyms=synonyms
        )
        assert result == '招商银行'
        assert method == 'synonym'

    def test_contains_match(self):
        result, conf, method = import_engine.normalize_value(
            'account', '招商银行储蓄卡',
            existing_values=['招商银行', '支付宝']
        )
        assert result == '招商银行'
        assert method == 'contains'

    def test_no_match(self):
        result, conf, method = import_engine.normalize_value(
            'account', '花旗银行',
            existing_values=['招商银行', '支付宝']
        )
        assert result == '花旗银行'
        assert method == 'original'


# ─── 来源检测 ──────────────────────────────────────────────

class TestDetectSource:
    def test_alipay(self):
        headers = ['交易创建时间', '交易对方', '商品说明', '金额']
        assert import_engine.detect_source(headers) == '支付宝'

    def test_wechat(self):
        headers = ['交易单号', '商户单号', '金额']
        assert import_engine.detect_source(headers) == '微信'

    def test_suishouji(self):
        headers = ['交易类型', '日期', '金额', '子类别']
        assert import_engine.detect_source(headers) == '随手记'

    def test_unknown(self):
        headers = ['a', 'b', 'c']
        assert import_engine.detect_source(headers) == '未知'

    def test_filename_hint(self):
        headers = ['col1', 'col2']
        assert import_engine.detect_source(headers, 'alipay_2024.csv') == '支付宝'


# ─── 预览与执行 ──────────────────────────────────────────────

class TestPreviewImport:
    def test_preview_basic(self, engine_db):
        csv_content = '交易类型,日期,金额,类别,备注\n支出,2024/06/15 10:00,100.50,餐饮,午饭\n收入,2024/06/15 14:00,5000,工资,工资\n'
        file_bytes = csv_content.encode('utf-8')

        result = import_engine.preview_import(file_bytes, filename='test.csv')

        assert result['total_rows'] == 2
        assert result['headers'] == ['交易类型', '日期', '金额', '类别', '备注']
        assert result['mapping']['交易类型']['target'] == 'type'
        assert result['mapping']['金额']['target'] == 'amount'
        assert len(result['preview_rows']) == 2
        assert result['preview_rows'][0]['type'] == '支出'
        assert result['preview_rows'][0]['amount'] == 100.50

    def test_preview_empty(self, engine_db):
        csv_content = 'col1,col2\n'
        result = import_engine.preview_import(csv_content.encode('utf-8'))
        assert result['total_rows'] == 0

    def test_preview_with_unmapped(self, engine_db):
        csv_content = '交易类型,日期,金额,订单号\n支出,2024/06/15 10:00,100,ORD001\n'
        result = import_engine.preview_import(csv_content.encode('utf-8'))
        assert '订单号' in result['unmapped_columns']


class TestExecuteImport:
    def test_execute_basic(self, engine_db):
        csv_content = '交易类型,日期,金额,类别,备注\n支出,2024/06/15 10:00,100.50,餐饮,午饭\n收入,2024/06/15 14:00,5000,工资,6月工资\n'
        file_bytes = csv_content.encode('utf-8')

        mapping = {
            '交易类型': 'type',
            '日期': 'date',
            '金额': 'amount',
            '类别': 'category',
            '备注': 'note',
        }

        result = import_engine.execute_import(
            file_bytes, mapping, tags=['测试导入'], filename='test.csv'
        )

        assert result['imported'] == 2
        assert result['skipped'] == 0
        assert result['batch_id'] is not None
        assert '测试导入' in result['tags_applied']

    def test_execute_with_extra_data(self, engine_db):
        csv_content = '交易类型,日期,金额,订单号\n支出,2024/06/15 10:00,100,ORD001\n'
        file_bytes = csv_content.encode('utf-8')

        mapping = {
            '交易类型': 'type',
            '日期': 'date',
            '金额': 'amount',
        }

        result = import_engine.execute_import(file_bytes, mapping)
        assert result['imported'] == 1

        # 验证 extra_data 被存储
        import sqlite3
        conn = sqlite3.connect(engine_db)
        c = conn.cursor()
        c.execute("SELECT extra_data FROM transactions ORDER BY id DESC LIMIT 1")
        extra = c.fetchone()[0]
        conn.close()
        assert extra is not None
        assert 'ORD001' in extra

    def test_execute_skip_invalid(self, engine_db):
        csv_content = '交易类型,日期,金额\n,2024/06/15 10:00,100\n支出,,100\n支出,2024/06/15,0\n支出,2024/06/15,50\n'
        file_bytes = csv_content.encode('utf-8')

        mapping = {'交易类型': 'type', '日期': 'date', '金额': 'amount'}
        result = import_engine.execute_import(file_bytes, mapping, skip_duplicates=False)

        # 只有最后一条是有效的
        assert result['imported'] == 1
        assert result['skipped'] >= 3

    def test_execute_batch_recorded(self, engine_db):
        csv_content = '交易类型,日期,金额\n支出,2024/06/15,100\n'
        file_bytes = csv_content.encode('utf-8')
        mapping = {'交易类型': 'type', '日期': 'date', '金额': 'amount'}

        result = import_engine.execute_import(
            file_bytes, mapping, tags=['微信导入'], filename='wechat.csv',
            batch_source='微信'
        )

        batch_id = result['batch_id']
        assert batch_id is not None

        import sqlite3
        conn = sqlite3.connect(engine_db)
        c = conn.cursor()
        c.execute("SELECT source, filename, row_count FROM import_batches WHERE id = ?", (batch_id,))
        row = c.fetchone()
        conn.close()
        assert row[0] == '微信'
        assert row[1] == 'wechat.csv'
        assert row[2] == 1


# ─── 别名管理 ──────────────────────────────────────────────

class TestSynonyms:
    def test_save_load(self, engine_db):
        test_synonyms = {
            'account': {'招商银行': ['招行', '招商']}
        }
        import_engine.save_synonyms(test_synonyms)
        loaded = import_engine.load_synonyms()
        assert loaded['account']['招商银行'] == ['招行', '招商']

    def test_empty_synonyms(self, engine_db):
        loaded = import_engine.load_synonyms()
        assert loaded == {}


# ─── 向后兼容 ──────────────────────────────────────────────

class TestBackwardCompat:
    def test_import_csv_compat(self, engine_db, tmp_path):
        csv_file = tmp_path / 'test.csv'
        csv_file.write_text('交易类型,日期,金额,类别,备注\n支出,2024/06/15 10:00,100,餐饮,午饭\n', encoding='utf-8')

        result = import_engine.import_csv_compat(str(csv_file))
        assert result is True

    def test_import_csv_compat_missing_file(self, engine_db):
        result = import_engine.import_csv_compat('/nonexistent/file.csv')
        assert result is False
