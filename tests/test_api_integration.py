#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger API 集成测试
使用 Flask test_client 测试所有 API 端点的实际效果。
不依赖外部服务，自动管理临时数据库。
"""

import json
import os
import sys
import tempfile
import shutil
import sqlite3

import pytest

# 确保项目根目录在 sys.path 中
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)

# 从 pyproject.toml 读取版本号
def _read_version():
    try:
        import tomllib
        with open(os.path.join(ROOT, 'pyproject.toml'), 'rb') as f:
            return tomllib.load(f).get('project', {}).get('version', '0.0.0')
    except Exception:
        return '0.0.0'

_VERSION = _read_version()

# ── 先劫持 DB 路径再导入 app ──
TEST_DIR = None
TEST_DB = None

def _setup_test_db():
    global TEST_DIR, TEST_DB
    TEST_DIR = tempfile.mkdtemp()
    TEST_DB = os.path.join(TEST_DIR, "test.db")
    os.environ["LEDGER_DB_PATH"] = TEST_DB
    return TEST_DB

def _teardown_test_db():
    global TEST_DIR
    if TEST_DIR and os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR, ignore_errors=True)
    if "LEDGER_DB_PATH" in os.environ:
        del os.environ["LEDGER_DB_PATH"]


# 必须先设置 DB 路径再导入 app
_setup_test_db()

# 现在导入 app（它会在模块加载时读 LEDGER_DB_PATH）
import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module
from web.app import app as flask_app


# ═══════════════════════════════════════════════════════════════════════════════
# pytest fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def reset_db():
    """每个测试前重置数据库状态"""
    # 重新初始化
    db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
    db_module.DB_PATH = db_path
    tx_module.DB_PATH = db_path
    budget_module.DB_PATH = db_path
    
    # 重建表（删掉所有数据）
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    tables = ["transactions", "budgets", "budget_templates", "record_templates"]
    for t in tables:
        c.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()
    conn.close()
    
    db_module.init_db()
    
    # 同步 web.app 模块中的 DB_PATH
    import web.app as web_app_module
    web_app_module.DB_PATH = db_path
    web_app_module.sync_db_path()
    
    yield
    
    # 每个测试后清理数据
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for t in tables:
        c.execute(f"DELETE FROM {t}")
    # 重置自增计数器
    c.execute("DELETE FROM sqlite_sequence")
    conn.commit()
    conn.close()


@pytest.fixture
def client():
    """Flask 测试客户端"""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _insert_sample_data(db_path):
    """插入示例数据"""
    tx_module.DB_PATH = db_path
    budget_module.DB_PATH = db_path
    
    tx_module.add_transaction("支出", 100.0, "食品酒水", "零食", "微信零钱",
                               "弹性支出", "本人", "拼多多", "零食",
                               "2026-06-15 10:00:00", force=True)
    tx_module.add_transaction("支出", 200.0, "行车交通", "打车租车", "支付宝",
                               "弹性支出", "本人", "滴滴", "打车",
                               "2026-06-14 14:30:00", force=True)
    tx_module.add_transaction("收入", 5000.0, "职业收入", "", "招商银行",
                               "", "本人", "", "6月工资",
                               "2026-06-10 09:00:00", force=True)
    tx_module.add_transaction("支出", 30.0, "食品酒水", "水果", "微信零钱",
                               "", "fish", "水果店", "水果",
                               "2026-06-12 18:00:00", force=True)


def _get_json(response):
    """解析 JSON 响应"""
    return json.loads(response.data.decode("utf-8"))


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：健康检查 & 信息
# ═══════════════════════════════════════════════════════════════════════════════


class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = _get_json(resp)
        assert data["status"] == "ok"
        assert data["version"] == _VERSION
        assert data["database"] is not None

    def test_health_also_at_health_path(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_info(self, client):
        resp = client.get("/api/info")
        assert resp.status_code == 200
        data = _get_json(resp)["data"]
        assert data["active_records"] == 0
        assert data["total_records"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：交易 CRUD
# ═══════════════════════════════════════════════════════════════════════════════


class TestTransactions:
    def test_add_transaction(self, client):
        resp = client.post("/api/transactions", json={
            "type": "支出", "amount": 25.5, "category": "食品酒水",
            "account": "微信零钱", "note": "零食",
        })
        assert resp.status_code == 200
        data = _get_json(resp)
        assert data["success"] is True
        assert data["data"]["id"] == 1

    def test_add_missing_amount(self, client):
        resp = client.post("/api/transactions", json={"type": "支出"})
        assert resp.status_code == 400
        data = _get_json(resp)
        assert data["success"] is False

    def test_add_empty_body(self, client):
        resp = client.post("/api/transactions", json=None,
                           content_type="application/json")
        assert resp.status_code == 400

    def test_duplicate_detection(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        # 同一条数据再添加一次
        resp = client.post("/api/transactions", json={
            "type": "支出", "amount": 100.0, "category": "食品酒水",
            "account": "微信零钱", "note": "零食",
            "date": "2026-06-15 10:00:00",
        })
        data = _get_json(resp)
        assert data["success"] is False
        assert "重复" in data["error"]

    def test_duplicate_force(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.post("/api/transactions", json={
            "type": "支出", "amount": 100.0, "category": "食品酒水",
            "account": "微信零钱", "note": "零食",
            "date": "2026-06-15 10:00:00", "force": True,
        })
        assert _get_json(resp)["success"] is True

    def test_list_transactions(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/transactions?limit=10")
        assert resp.status_code == 200
        data = _get_json(resp)["data"]
        assert data["total"] == 4
        assert len(data["transactions"]) == 4

    def test_list_pagination(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/transactions?limit=2&offset=0")
        data = _get_json(resp)["data"]
        assert len(data["transactions"]) == 2
        assert data["total"] == 4

    def test_get_transaction(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/transactions/1")
        assert resp.status_code == 200
        data = _get_json(resp)["data"]
        assert data["id"] == 1
        assert data["amount"] == 100.0
        assert data["category"] == "食品酒水"

    def test_get_transaction_not_found(self, client):
        resp = client.get("/api/transactions/999")
        assert resp.status_code == 404

    def test_update_transaction(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.put("/api/transactions/1", json={
            "field": "amount", "value": 50.0,
        })
        assert _get_json(resp)["success"] is True

    def test_update_invalid_field(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.put("/api/transactions/1", json={
            "field": "invalid_field", "value": "test",
        })
        assert _get_json(resp)["success"] is False

    def test_update_missing_params(self, client):
        resp = client.put("/api/transactions/1", json={})
        assert _get_json(resp)["success"] is False

    def test_soft_delete(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.delete("/api/transactions/1")
        assert _get_json(resp)["success"] is True
        # 确认软删除
        resp = client.get("/api/transactions/1")
        assert _get_json(resp)["data"]["is_deleted"] is True

    def test_restore(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        client.delete("/api/transactions/1")
        resp = client.post("/api/transactions/1/restore")
        assert _get_json(resp)["success"] is True

    def test_soft_delete_excludes_from_list(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        client.delete("/api/transactions/1")
        resp = client.get("/api/transactions?limit=10")
        assert _get_json(resp)["data"]["total"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：搜索 & 筛选
# ═══════════════════════════════════════════════════════════════════════════════


class TestSearch:
    def test_search_by_keyword(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/transactions/search?keyword=拼多多")
        assert resp.status_code == 200
        data = _get_json(resp)
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert "拼多多" in data["data"][0].get("note", "") or \
               "拼多多" in data["data"][0].get("category", "") or \
               data["data"][0]["id"] == 1

    def test_search_no_results(self, client):
        resp = client.get("/api/transactions/search?keyword=不存在的关键词")
        assert resp.status_code == 200
        assert _get_json(resp)["data"] == []

    def test_search_missing_keyword(self, client):
        resp = client.get("/api/transactions/search")
        assert _get_json(resp)["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：汇总 & 统计
# ═══════════════════════════════════════════════════════════════════════════════


class TestSummary:
    def test_summary_all(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/summary")
        data = _get_json(resp)["data"]
        assert data["expense"] == 330.0  # 100 + 200 + 30
        assert data["income"] == 5000.0
        assert data["balance"] == 4670.0  # 5000 - 330

    def test_summary_with_deleted(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        client.delete("/api/transactions/1")
        resp = client.get("/api/summary")
        data = _get_json(resp)["data"]
        assert data["expense"] == 230.0  # 200 + 30（100 的已被软删除）


class TestStats:
    def test_stats_by_category(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/stats?group_by=category")
        data = _get_json(resp)["data"]
        assert data["group_by"] == "category"
        assert len(data["items"]) >= 2

    def test_stats_by_account(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/stats?group_by=account")
        data = _get_json(resp)["data"]
        assert data["group_by"] == "account"

    def test_stats_by_month(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/stats?group_by=month")
        data = _get_json(resp)["data"]
        assert data["group_by"] == "month"

    def test_stats_invalid_group(self, client):
        resp = client.get("/api/stats?group_by=invalid")
        assert _get_json(resp)["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：类别 / 账户 / 成员
# ═══════════════════════════════════════════════════════════════════════════════


class TestMetaData:
    def test_categories(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/categories")
        data = _get_json(resp)["data"]
        assert len(data) >= 2  # 食品酒水、行车交通
        cats = {c["name"]: c for c in data}
        assert "食品酒水" in cats
        assert cats["食品酒水"]["total_count"] == 2  # 零食 + 水果

    def test_accounts(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/accounts")
        data = _get_json(resp)["data"]
        assert len(data) >= 3  # 微信零钱、支付宝、招商银行
        names = [a["name"] for a in data]
        assert "微信零钱" in names
        assert "招商银行" in names

    def test_members(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/members")
        data = _get_json(resp)["data"]
        names = [m["name"] for m in data]
        assert "本人" in names
        assert "fish" in names


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：预算
# ═══════════════════════════════════════════════════════════════════════════════


class TestBudgets:
    def test_set_budget(self, client):
        resp = client.post("/api/budgets", json={
            "category": "食品酒水", "amount": 1000,
            "year": 2026, "month": 6,
        })
        assert _get_json(resp)["success"] is True

    def test_set_budget_missing_params(self, client):
        resp = client.post("/api/budgets", json={})
        assert _get_json(resp)["success"] is False

    def test_list_budgets(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        # 设置预算
        client.post("/api/budgets", json={
            "category": "食品酒水", "amount": 1000, "year": 2026, "month": 6,
        })
        resp = client.get("/api/budgets?year=2026&month=6")
        data = _get_json(resp)["data"]
        assert len(data) >= 1
        budget = next(b for b in data if b["category"] == "食品酒水")
        assert budget["amount"] == 1000
        assert budget["spent"] == 130.0  # 零食 100 + 水果 30
        assert budget["remaining"] == 870.0

    def test_budget_check(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        client.post("/api/budgets", json={
            "category": "食品酒水", "amount": 100, "year": 2026, "month": 6,
        })
        resp = client.get("/api/budgets/check?year=2026&month=6")
        data = _get_json(resp)["data"]
        assert len(data) >= 1
        # 预算 100，花了 130，超支
        b = next(x for x in data if x["category"] == "食品酒水")
        assert b["percentage"] == 130.0


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：导出
# ═══════════════════════════════════════════════════════════════════════════════


class TestExport:
    def test_export_json(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/export?format=json")
        data = _get_json(resp)["data"]
        assert data["count"] == 4
        assert data["format"] == "json"
        assert len(data["data"]) == 4

    def test_export_empty(self, client):
        resp = client.get("/api/export")
        assert _get_json(resp)["success"] is False

    def test_export_filter_category(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/export?format=json&category=食品酒水")
        data = _get_json(resp)["data"]
        assert data["count"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：数据分析
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnalyze:
    def test_analyze_returns_report(self, client, reset_db):
        db_path = os.environ.get("LEDGER_DB_PATH", TEST_DB)
        _insert_sample_data(db_path)
        resp = client.get("/api/analyze")
        data = _get_json(resp)["data"]
        assert "report" in data
        report = data["report"]
        assert "数据分析报告" in report
        assert "食品酒水" in report
        assert "本人" in report


# ═══════════════════════════════════════════════════════════════════════════════
# 测试：错误处理 & 边界
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    def test_404_unexpected_path(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code in (404, 405)

    def test_invalid_json_body(self, client):
        resp = client.post("/api/transactions",
                           data="not json",
                           content_type="application/json")
        # Flask 默认返回 400
        assert resp.status_code in (400, 415)

    def test_negative_amount(self, client):
        resp = client.post("/api/transactions", json={
            "type": "支出", "amount": -100, "category": "测试",
        })
        data = _get_json(resp)
        # 应该允许负数作为支出？取决于业务逻辑
        # 至少确保不崩溃
        assert "success" in data

    def test_very_large_limit(self, client):
        """大数据量极限测试"""
        resp = client.get("/api/transactions?limit=999999")
        assert resp.status_code == 200

    def test_concurrent_requests(self, client, reset_db):
        """快速连续请求不崩"""
        for i in range(20):
            resp = client.post("/api/transactions", json={
                "type": "支出" if i % 2 == 0 else "收入",
                "amount": float(i + 1),
                "category": "测试",
                "note": f"批量测试{i}",
                "force": True,
            })
            assert resp.status_code == 200
        resp = client.get("/api/transactions?limit=100")
        data = _get_json(resp)["data"]
        assert data["total"] == 20


# ═══════════════════════════════════════════════════════════════════════════════
# 清理
# ═══════════════════════════════════════════════════════════════════════════════


def pytest_unconfigure():
    """所有测试结束后清理临时文件"""
    _teardown_test_db()
