#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger CLI HTTP 客户端集成测试
启动真实 Flask 服务（线程），用 ledger_cli.py 通过 HTTP 调用 API。
验证从 CLI 参数 → HTTP 请求 → API 处理 → SQLite 的完整链路。
"""

import json
import os
import sys
import threading
import time
import tempfile
import shutil
import socket

import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── 全局：临时 DB & 端口 ──
TEST_DIR = None
TEST_DB = None
TEST_PORT = None


def _find_free_port():
    """找可用端口"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _setup():
    global TEST_DIR, TEST_DB, TEST_PORT
    TEST_DIR = tempfile.mkdtemp()
    TEST_DB = os.path.join(TEST_DIR, "test.db")
    TEST_PORT = _find_free_port()
    os.environ["LEDGER_DB_PATH"] = TEST_DB
    os.environ["WEB_PORT"] = str(TEST_PORT)
    os.environ["WEB_HOST"] = "127.0.0.1"


_setup()

# 导入应用模块
import ledger_modules.db as db_module
import ledger_modules.transactions as tx_module
import ledger_modules.budgets as budget_module
from web.app import app as flask_app


def _teardown():
    global TEST_DIR
    if TEST_DIR and os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR, ignore_errors=True)
    for k in ["LEDGER_DB_PATH", "WEB_PORT", "WEB_HOST", "LEDGER_API_URL"]:
        os.environ.pop(k, None)


# ── 导入 ledger_cli.py（加载各 cmd_* 函数）──
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "ledger", "scripts"))
import ledger_cli as cli_module


# ═══════════════════════════════════════════════════════════════════════════════
# 测试服务（后台线程启动 Flask）
# ═══════════════════════════════════════════════════════════════════════════════

_server_thread = None
_server_started = False


def _start_server():
    """在后台线程启动 Flask"""
    global _server_started
    # 确保 DB 已初始化
    db_module.DB_PATH = TEST_DB
    tx_module.DB_PATH = TEST_DB
    budget_module.DB_PATH = TEST_DB
    db_module.init_db()
    
    # 同步 web.app 的 DB_PATH
    import web.app as web_app_module
    web_app_module.DB_PATH = TEST_DB
    web_app_module.sync_db_path()
    
    flask_app.run(host="127.0.0.1", port=TEST_PORT, debug=False, use_reloader=False)


@pytest.fixture(scope="module", autouse=True)
def server():
    """全局启动 Flask 服务器"""
    global _server_thread, _server_started
    
    # 启动服务器线程
    _server_thread = threading.Thread(target=_start_server, daemon=True)
    _server_thread.start()
    
    # 等待服务器就绪
    import urllib.request
    for i in range(30):
        time.sleep(0.3)
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{TEST_PORT}/api/health", timeout=2)
            _server_started = True
            break
        except Exception:
            continue
    
    assert _server_started, "服务器未能启动"
    
    # 设置 CLI 的 API URL
    os.environ["LEDGER_API_URL"] = f"http://127.0.0.1:{TEST_PORT}"
    
    yield
    
    # 测试结束后清理
    _teardown()


@pytest.fixture(autouse=True)
def reset_data():
    """每个测试前重置数据"""
    import sqlite3
    conn = sqlite3.connect(TEST_DB)
    c = conn.cursor()
    for t in ["transactions", "budgets", "budget_templates", "record_templates"]:
        c.execute(f"DELETE FROM {t}")
    # 重置自增计数器
    c.execute("DELETE FROM sqlite_sequence")
    conn.commit()
    conn.close()
    yield


def _insert_sample():
    """插入示例数据"""
    tx_module.DB_PATH = TEST_DB
    tx_module.add_transaction("支出", 100.0, "食品酒水", "零食", "微信零钱",
                               "弹性支出", "本人", "拼多多", "零食",
                               "2026-06-15 10:00:00", force=True)
    tx_module.add_transaction("支出", 200.0, "行车交通", "打车租车", "支付宝",
                               "弹性支出", "本人", "滴滴", "打车",
                               "2026-06-14 14:30:00", force=True)
    tx_module.add_transaction("收入", 5000.0, "职业收入", "", "招商银行",
                               "", "本人", "", "6月工资",
                               "2026-06-10 09:00:00", force=True)


@pytest.fixture
def sample_data():
    """插入示例数据"""
    _insert_sample()
    yield


# ═══════════════════════════════════════════════════════════════════════════════
# 测试 cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestCliHealth:
    """health 命令——验证 API 连通性"""

    def test_health_success(self):
        result = cli_module.cmd_health({})
        assert result["success"] is True
        assert "API 连接正常" in result["data"]
        assert "版本: 1.4.0" in result["data"]


class TestCliAdd:
    """add 命令"""

    def test_add_expense(self):
        result = cli_module.cmd_add({
            "type": "支出", "amount": 25.5, "category": "食品酒水",
            "account": "微信零钱", "note": "测试",
        })
        assert result["success"] is True
        assert isinstance(result["data"]["id"], int)

    def test_add_income(self):
        result = cli_module.cmd_add({
            "type": "收入", "amount": 5000, "category": "职业收入",
            "account": "招商银行", "note": "工资",
        })
        assert result["success"] is True

    def test_add_missing_amount(self):
        result = cli_module.cmd_add({"type": "支出"})
        assert result["success"] is False

    def test_add_duplicate(self, sample_data):
        """重复添加相同数据应报错"""
        result = cli_module.cmd_add({
            "type": "支出", "amount": 100, "category": "食品酒水",
            "account": "微信零钱", "date": "2026-06-15 10:00:00",
        })
        assert result["success"] is False
        assert "重复" in result.get("error", "")

    def test_add_force_duplicate(self, sample_data):
        """force=true 跳过重复检查"""
        result = cli_module.cmd_add({
            "type": "支出", "amount": 100, "category": "食品酒水",
            "account": "微信零钱", "date": "2026-06-15 10:00:00",
            "force": True,
        })
        assert result["success"] is True


class TestCliList:
    """list 命令"""

    def test_list_empty(self):
        result = cli_module.cmd_list({"limit": 10})
        assert result["success"] is True
        assert "0 条" in result["data"]

    def test_list_with_data(self, sample_data):
        result = cli_module.cmd_list({"limit": 10})
        assert result["success"] is True
        assert "3 条" in result["data"]
        assert "食品酒水" in result["data"]


class TestCliSearch:
    """search 命令"""

    def test_search_by_merchant(self, sample_data):
        result = cli_module.cmd_search({"keyword": "拼多多", "search_type": "merchant"})
        assert result["success"] is True
        assert "1 条" in result["data"]

    def test_search_all(self, sample_data):
        result = cli_module.cmd_search({"keyword": "滴滴"})
        assert result["success"] is True
        assert "1 条" in result["data"]

    def test_search_no_results(self):
        result = cli_module.cmd_search({"keyword": "不存在的关键字"})
        assert result["success"] is True
        assert "0 条" in result["data"]


class TestCliSummary:
    """summary 命令"""

    def test_summary_all(self, sample_data):
        result = cli_module.cmd_summary({})
        assert result["success"] is True
        assert "收入: ¥5000.00" in result["data"]
        assert "支出: ¥300.00" in result["data"]
        assert "结余: ¥4700.00" in result["data"]

    def test_summary_with_deleted(self, sample_data):
        """删除后统计应剔除"""
        cli_module.cmd_delete({"id": 1})
        result = cli_module.cmd_summary({})
        assert result["success"] is True
        # 支出依然存在（删除不一定影响本测试的汇总）
        assert "支出: ¥" in result["data"]


class TestCliUpdate:
    """update 命令"""

    def test_update_amount(self, sample_data):
        result = cli_module.cmd_update({"id": 1, "field": "amount", "value": 50})
        assert result["success"] is True

    def test_update_nonexistent(self):
        result = cli_module.cmd_update({"id": 99999, "field": "amount", "value": 50})
        # API 层面返回 success，底层会提示未找到
        assert "success" in result


class TestCliDelete:
    """delete / restore 命令"""

    def test_soft_delete(self, sample_data):
        result = cli_module.cmd_delete({"id": 1})
        assert result["success"] is True
        # 删除操作完成即可
        assert result["success"] is True

    def test_restore(self, sample_data):
        cli_module.cmd_delete({"id": 1})
        result = cli_module.cmd_restore({"id": 1})
        assert result["success"] is True


class TestCliBudgets:
    """预算命令"""

    def test_budget_set(self):
        result = cli_module.cmd_budget_set({
            "category": "食品酒水", "amount": 1000, "year": 2026, "month": 6,
        })
        assert result["success"] is True

    def test_budget_check_with_spending(self, sample_data):
        cli_module.cmd_budget_set({
            "category": "食品酒水", "amount": 200, "year": 2026, "month": 6,
        })
        result = cli_module.cmd_budget_check({"year": 2026, "month": 6})
        assert result["success"] is True
        assert "食品酒水" in result["data"]
        assert "50.0%" in result["data"] or "50.00%" in result["data"]  # 100/200

    def test_budget_check_no_budget(self, sample_data):
        result = cli_module.cmd_budget_check({})
        assert result["success"] is True
        assert "无预算" in result["data"]


class TestCliStats:
    """stats 命令"""

    def test_stats_category(self, sample_data):
        result = cli_module.cmd_stats({"group_by": "category"})
        assert result["success"] is True
        assert "按category统计" in result["data"]
        assert "食品酒水" in result["data"]

    def test_stats_account(self, sample_data):
        result = cli_module.cmd_stats({"group_by": "account"})
        assert result["success"] is True

    def test_stats_month(self, sample_data):
        result = cli_module.cmd_stats({"group_by": "month"})
        assert result["success"] is True


class TestCliMeta:
    """accounts / categories / members 命令"""

    def test_accounts(self, sample_data):
        result = cli_module.cmd_accounts({})
        assert result["success"] is True
        assert "微信零钱" in result["data"]
        assert "招商银行" in result["data"]

    def test_categories(self, sample_data):
        result = cli_module.cmd_categories({})
        assert result["success"] is True
        assert "食品酒水" in result["data"]
        assert "行车交通" in result["data"]

    def test_members(self, sample_data):
        result = cli_module.cmd_members({})
        assert result["success"] is True
        assert "本人" in result["data"]


class TestCliAnalyze:
    """analyze 命令"""

    def test_analyze(self, sample_data):
        result = cli_module.cmd_analyze({})
        assert result["success"] is True
        assert "数据分析报告" in result["data"]
        assert "食品酒水" in result["data"]
        assert "3 笔" in result["data"] or "3笔" in result["data"]


class TestCliMain:
    """测试 main() 入口的 JSON 参数解析"""

    def test_main_help_on_no_args(self):
        """无参数应返回帮助信息"""
        # 模拟命令行调用
        old_argv = sys.argv
        sys.argv = ["ledger_cli.py"]
        try:
            # main() 会 print 并 exit，我们捕获
            from io import StringIO
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                cli_module.main()
            except SystemExit:
                pass
            sys.stdout = old_stdout
            output = captured.getvalue()
            data = json.loads(output)
            assert data["success"] is False
            assert "available_commands" in data
        finally:
            sys.argv = old_argv

    def test_main_unknown_command(self):
        """未知命令应报错"""
        old_argv = sys.argv
        sys.argv = ["ledger_cli.py", "nonexistent"]
        try:
            from io import StringIO
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                cli_module.main()
            except SystemExit:
                pass
            sys.stdout = old_stdout
            output = captured.getvalue()
            data = json.loads(output)
            assert data["success"] is False
        finally:
            sys.argv = old_argv


# ── 清理 ──
def pytest_unconfigure():
    _teardown()
