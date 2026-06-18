#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ledger API 手动测试脚本
一键运行，测试所有核心 API 是否正常。

用法：
    python scripts/test_api.py                  # 测试 127.0.0.1:5800
    python scripts/test_api.py --url http://192.168.31.126:5800
    python scripts/test_api.py --port 5800
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# 添加项目根目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# GBK 安全打印
def _print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('ascii', 'replace').decode('ascii'))


def _req(method, url, data=None):
    """发送 HTTP 请求，返回 JSON"""
    if data is not None and isinstance(data, dict):
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={'Content-Type': 'application/json',
                                          'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode('utf-8'))
            return body
        except Exception:
            return {'success': False, 'error': f'HTTP {e.code}: {e.reason}'}
    except urllib.error.URLError as e:
        return {'success': False, 'error': f'连不上: {e.reason}。确认服务已启动？'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def test(api_url):
    passed = 0
    failed = 0
    results = []

    def check(name, success, detail=''):
        nonlocal passed, failed
        if success:
            passed += 1
            results.append(f'  [PASS] {name}')
        else:
            failed += 1
            results.append(f'  [FAIL] {name}  {detail}')

    print(f'\n测试 Ledger API: {api_url}\n')
    print('=' * 50)

    # 1. 健康检查
    r = _req('GET', f'{api_url}/api/health')
    check('健康检查 /api/health',
          r.get('status') == 'ok',
          f'status={r.get("status")}')

    # 2. DB 信息
    r = _req('GET', f'{api_url}/api/info')
    check('数据库信息 /api/info',
          r.get('success') and r['data'].get('total_records', 0) >= 0,
          f"共 {r.get('data',{}).get('total_records',0)} 条记录")

    # 3. 获取交易列表
    r = _req('GET', f'{api_url}/api/transactions?limit=3')
    if r.get('success'):
        total = r['data'].get('total', 0)
        check('交易列表 /api/transactions', total > 0,
              f'{total} 条记录')
    else:
        check('交易列表 /api/transactions', False, r.get('error', ''))

    # 4. 新增一笔交易（force=True 跳过重复检测）
    r = _req('POST', f'{api_url}/api/transactions', {
        'type': '支出', 'amount': 15.5, 'category': '测试类别',
        'account': '手动测试', 'note': 'API测试脚本',
        'force': True,
    })
    new_id = r.get('data', {}).get('id')
    check('新增交易 POST /api/transactions',
          r.get('success'),
          f"id={new_id}")

    # 5. 获取单笔交易（用刚新增的 ID）
    rid = new_id or 1
    r = _req('GET', f'{api_url}/api/transactions/{rid}')
    check('获取单笔 GET /api/transactions/{rid}',
          r.get('success'),
          f"category={r.get('data',{}).get('category','?')}")

    # 6. 修改交易
    r = _req('PUT', f'{api_url}/api/transactions/{rid}',
             {'field': 'note', 'value': '已修改'})
    check('修改交易 PUT /api/transactions/{rid}',
          r.get('success'))

    # 7. 软删除
    r = _req('DELETE', f'{api_url}/api/transactions/{rid}')
    check('软删除 DELETE /api/transactions/{rid}',
          r.get('success'))

    # 8. 恢复
    r = _req('POST', f'{api_url}/api/transactions/{rid}/restore')
    check('恢复 POST /api/transactions/{rid}/restore',
          r.get('success'))

    # 9. 搜索（中文关键词需要 URL 编码）
    from urllib.parse import urlencode, quote
    search_url = f'{api_url}/api/transactions/search?{urlencode({"keyword": "测试类别"})}'
    r = _req('GET', search_url)
    check('搜索 /api/transactions/search',
          r.get('success'))

    # 10. 收支汇总
    r = _req('GET', f'{api_url}/api/summary')
    check('收支汇总 /api/summary',
          r.get('success'),
          f"收入={r.get('data',{}).get('income',0):.0f} 支出={r.get('data',{}).get('expense',0):.0f}")

    # 11. 统计
    r = _req('GET', f'{api_url}/api/stats?group_by=category')
    check('统计分析 /api/stats',
          r.get('success'))

    # 12. 类别列表
    r = _req('GET', f'{api_url}/api/categories')
    check('类别列表 /api/categories',
          r.get('success') and len(r.get('data', [])) > 0,
          f"{len(r.get('data',[]))} 个类别")

    # 13. 账户列表
    r = _req('GET', f'{api_url}/api/accounts')
    check('账户列表 /api/accounts',
          r.get('success') and len(r.get('data', [])) > 0,
          f"{len(r.get('data',[]))} 个账户")

    # 14. 设置预算
    r = _req('POST', f'{api_url}/api/budgets', {
        'category': '测试', 'amount': 1000, 'year': 2026, 'month': 6,
    })
    check('设置预算 POST /api/budgets',
          r.get('success'))

    # 15. 检查预算
    r = _req('GET', f'{api_url}/api/budgets/check?year=2026&month=6')
    check('预算检查 /api/budgets/check',
          r.get('success') and len(r.get('data', [])) > 0,
          f"{len(r.get('data',[]))} 条预算")

    # 16. 导出
    r = _req('GET', f'{api_url}/api/export?format=json')
    check('导出数据 /api/export',
          r.get('success') and r.get('data', {}).get('count', 0) > 0,
          f"{r.get('data',{}).get('count',0)} 条")

    # 17. 数据分析
    r = _req('GET', f'{api_url}/api/analyze')
    report_text = ''
    if isinstance(r.get('data'), dict):
        report_text = r.get('data', {}).get('report', '')
    elif isinstance(r.get('data'), str):
        report_text = r.get('data', '')
    check('数据分析 /api/analyze',
          r.get('success') and len(report_text) > 100,
          f"含 {len(report_text)} 字符报告")

    # 输出结果
    _print('\n' + '=' * 50)
    for r in results:
        _print(r)
    _print('')
    _print(f'总计: {passed + failed}  通过: {passed}  失败: {failed}')
    if failed > 0:
        _print(f'\n警告: 有失败的测试，检查服务是否启动在 {api_url}')
    else:
        _print('\n全部通过! API 正常。')

    return failed == 0


def main():
    parser = argparse.ArgumentParser(description='Ledger API 手动测试')
    parser.add_argument('--url', default='http://127.0.0.1:5800',
                        help='API 地址（默认 http://127.0.0.1:5800）')
    parser.add_argument('--port', type=int, help='端口（快捷方式，覆盖 url 中的端口）')
    args = parser.parse_args()

    api_url = args.url.rstrip('/')
    if args.port:
        # 替换端口
        from urllib.parse import urlparse
        parts = urlparse(api_url)
        api_url = f'{parts.scheme}://{parts.hostname}:{args.port}'

    success = test(api_url)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
