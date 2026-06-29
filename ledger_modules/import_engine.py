"""
智能导入引擎

功能：
- CSV 编码检测（UTF-8 / GBK / GB2312）
- 列名语义推断（内置模式匹配 + 可配置）
- 值标准化（基于用户现有数据 + synonyms 别名配置）
- 预览模式（返回映射建议 + 样本数据 + 标签建议）
- 执行模式（映射 → 转换 → 去重检测 → 入库 → 打标签）
- extra_data 存储映射不了的列值
"""

import csv
import io
import json
import os
import re
import sqlite3
from datetime import datetime

try:
    import chardet
except ImportError:
    chardet = None

from .db import DB_PATH
from .transaction_types import (
    TYPE_ALIASES,
    EXPENSE,
    INCOME,
    RECONCILIATION,
    TRANSFER,
    normalize_raw_type,
)

# ─── 列名推断模式 ──────────────────────────────────────────

FIELD_PATTERNS = {
    'type': ['交易类型', '类型', '收/支', '收支类型', 'type', '收支方向', 'income/expense'],
    'amount': ['金额', '金额(元)', '支付金额', '交易金额', 'amount', '金额（元）', '交易金额(元)', '实付金额'],
    'date': ['日期', '交易时间', '交易日期', '记账时间', 'date', '时间', '交易创建时间', '付款时间'],
    'category': ['类别', '分类', '交易分类', 'category', '一级分类', '交易类别'],
    'subcategory': ['子类别', '子分类', '二级分类', 'subcategory'],
    'account': ['账户', '支付方式', '资金渠道', '付款方式', 'account', '收/付款方式', '资金账户'],
    'merchant': ['商家', '交易对方', '对方', '商户', 'merchant', '交易商户', '对方名称', '商户名称'],
    'member': ['成员', '交易人', 'member', '记账人', '操作人'],
    'project': ['项目', 'project'],
    'note': ['备注', '商品说明', '商品名称', '交易说明', 'note', '商品描述', '描述', '交易备注'],
}

# 字段的重要性：必填字段如果匹配不到要提醒用户
REQUIRED_FIELDS = {'type', 'amount', 'date'}
OPTIONAL_FIELDS = {'category', 'subcategory', 'account', 'merchant', 'member', 'project', 'note'}

# 日期格式尝试顺序
DATE_FORMATS = [
    '%Y/%m/%d %H:%M',
    '%Y/%m/%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%Y/%m/%d',
    '%Y-%m-%d',
    '%Y%m%d %H:%M:%S',
    '%Y%m%d %H:%M',
    '%Y%m%d',
    '%m/%d/%Y %H:%M',
    '%m/%d/%Y',
]


# ─── 编码检测 ──────────────────────────────────────────────

def detect_encoding(file_bytes):
    """检测文件编码，返回编码名称"""
    # 优先尝试 UTF-8 BOM
    if file_bytes[:3] == b'\xef\xbb\xbf':
        return 'utf-8-sig'

    # 尝试 UTF-8
    try:
        file_bytes.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        pass

    # 用 chardet 检测
    if chardet:
        result = chardet.detect(file_bytes)
        if result and result.get('encoding'):
            enc = result['encoding'].lower()
            # chardet 有时返回 GB2312，实际用 GBK 更安全
            if enc in ('gb2312', 'gbk', 'gb18030'):
                return 'gbk'
            return enc

    # 兜底
    return 'utf-8'


def parse_csv(file_bytes, encoding=None):
    """
    解析 CSV 文件，返回 (headers, rows, encoding)

    rows 是 list[dict]，每个 dict 是一行数据
    """
    if encoding is None:
        encoding = detect_encoding(file_bytes)

    text = file_bytes.decode(encoding, errors='replace')

    # 尝试检测分隔符
    dialect = csv.Sniffer().sniff(text[:4096])
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)

    headers = reader.fieldnames or []
    rows = []
    for row in reader:
        rows.append(row)

    return headers, rows, encoding


# ─── 列名推断 ──────────────────────────────────────────────

def infer_mapping(headers):
    """
    推断 CSV 列名到系统字段的映射

    返回 dict: { csv列名: { target: 'field_name'|None, confidence: 0.0~1.0 } }
    """
    mapping = {}

    for header in headers:
        header_clean = header.strip().lower()
        best_match = None
        best_score = 0.0

        for field, patterns in FIELD_PATTERNS.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                # 完全匹配
                if header_clean == pattern_lower:
                    best_match = field
                    best_score = 1.0
                    break
                # 包含匹配
                if pattern_lower in header_clean or header_clean in pattern_lower:
                    score = 0.8
                    if score > best_score:
                        best_match = field
                        best_score = score
                        break
            if best_score >= 1.0:
                break

        mapping[header] = {
            'target': best_match,
            'confidence': best_score,
        }

    return mapping


def _resolve_mapping_conflicts(mapping):
    """
    解决映射冲突：如果多个列映射到同一个字段，保留置信度最高的

    返回修正后的 mapping
    """
    # 收集每个 target 的所有候选
    target_candidates = {}
    for header, info in mapping.items():
        target = info.get('target')
        if target:
            if target not in target_candidates:
                target_candidates[target] = []
            target_candidates[target].append((header, info.get('confidence', 0)))

    # 找出冲突并解决
    for target, candidates in target_candidates.items():
        if len(candidates) <= 1:
            continue
        # 按置信度排序，保留最高的
        candidates.sort(key=lambda x: x[1], reverse=True)
        winner = candidates[0][0]
        for header, _ in candidates:
            if header != winner:
                mapping[header]['target'] = None
                mapping[header]['confidence'] = 0

    return mapping


# ─── 值标准化 ──────────────────────────────────────────────

def get_existing_values(field):
    """从数据库获取某个字段的所有已有值（去重）"""
    # 字段名映射到数据库列名
    db_field_map = {
        'type': 'type',
        'category': 'category',
        'subcategory': 'subcategory',
        'account': 'account',
        'merchant': 'merchant',
        'member': 'member',
        'project': 'project',
    }
    db_field = db_field_map.get(field)
    if not db_field:
        return []

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"""SELECT DISTINCT {db_field}
                      FROM transactions
                      WHERE is_deleted = 0 AND {db_field} IS NOT NULL AND {db_field} != ''
                      ORDER BY {db_field}""")
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:
        return []


def load_synonyms():
    """从数据库加载别名配置"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM meta WHERE key = 'synonyms'")
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
    except Exception:
        pass
    return {}


def save_synonyms(synonyms):
    """保存别名配置到数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('synonyms', ?)",
              (json.dumps(synonyms, ensure_ascii=False),))
    conn.commit()
    conn.close()


def normalize_value(field, raw_value, existing_values=None, synonyms=None):
    """
    标准化一个字段的值

    1. 先查 synonyms 别名表
    2. 再在 existing_values 里做模糊匹配
    3. 都匹配不到就原样返回

    返回 (normalized_value, confidence, match_method)
    """
    if not raw_value or not raw_value.strip():
        return raw_value, 0, 'empty'

    raw_clean = raw_value.strip()

    # 1. 查别名表
    if synonyms and field in synonyms:
        field_synonyms = synonyms[field]
        for standard_name, alias_list in field_synonyms.items():
            if raw_clean == standard_name:
                return standard_name, 1.0, 'exact'
            for alias in alias_list:
                if raw_clean == alias:
                    return standard_name, 0.95, 'synonym'
                # 包含匹配
                if alias in raw_clean or raw_clean in alias:
                    return standard_name, 0.8, 'synonym_partial'

    # 2. 在已有值里匹配
    if existing_values:
        # 完全匹配
        for val in existing_values:
            if raw_clean == val:
                return val, 1.0, 'exact'

        # 包含匹配（较短的包含在较长的中）
        for val in existing_values:
            if val in raw_clean or raw_clean in val:
                return val, 0.7, 'contains'

    # 3. 原样返回
    return raw_clean, 0, 'original'


def normalize_type(raw_value):
    """标准化交易类型"""
    return normalize_raw_type(raw_value)


def normalize_amount(raw_value):
    """标准化金额"""
    if not raw_value:
        return None
    raw = raw_value.strip()
    # 去掉货币符号和千分位
    raw = raw.replace('¥', '').replace('￥', '').replace(',', '').replace(' ', '')
    try:
        amount = float(raw)
        return amount
    except (ValueError, TypeError):
        return None


def normalize_date(raw_value):
    """标准化日期，返回 YYYY-MM-DD HH:MM:SS 格式"""
    if not raw_value:
        return None
    raw = raw_value.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    return None


def detect_source(headers, filename=''):
    """
    从列名和文件名推断数据来源

    返回: "支付宝" / "微信" / "银行" / "随手记" / "未知"
    """
    header_set = set(h.strip() for h in headers)
    header_text = ' '.join(h.lower() for h in headers)
    fn = filename.lower()

    # 支付宝特征
    alipay_hints = {'交易对方', '商品说明', '交易创建时间', '支付宝'}
    if any(h in header_set for h in alipay_hints) or 'alipay' in fn or '支付宝' in fn:
        return '支付宝'

    # 微信特征
    wechat_hints = {'交易单号', '商户单号', '支付方式'}
    if any(h in header_set for h in wechat_hints) or 'wechat' in fn or '微信' in fn:
        return '微信'

    # 随手记特征
    if '交易类型' in header_set and '子类别' in header_set:
        return '随手记'

    # 银行特征
    bank_hints = {'借方', '贷方', '余额', '凭证号', '交易摘要'}
    if any(h in header_set for h in bank_hints) or 'bank' in fn or '银行' in fn:
        return '银行'

    return '未知'


def suggest_tags(source, rows):
    """根据来源生成标签建议"""
    tags = []

    # 来源标签
    source_tag_map = {
        '支付宝': '支付宝导入',
        '微信': '微信导入',
        '银行': '银行对账单',
        '随手记': '随手记导入',
    }
    if source in source_tag_map:
        tags.append(source_tag_map[source])

    return tags


# ─── 预览与执行 ──────────────────────────────────────────────

def preview_import(file_bytes, user_mapping=None, filename=''):
    """
    预览导入：解析 CSV，推断映射，返回预览数据

    返回:
    {
        "detected_source": "支付宝",
        "encoding": "utf-8",
        "headers": [...],
        "mapping": { csv列名: { target, confidence } },
        "unmapped_columns": [...],
        "preview_rows": [...前5行转换后数据...],
        "total_rows": 128,
        "suggested_tags": [...],
        "duplicate_estimate": 3
    }
    """
    # 解析 CSV
    headers, rows, encoding = parse_csv(file_bytes)
    if not headers or not rows:
        return {
            'error': 'CSV 文件为空或无法解析',
            'headers': [],
            'mapping': {},
            'total_rows': 0,
        }

    # 推断列映射
    if user_mapping:
        mapping = {}
        for header in headers:
            target = user_mapping.get(header)
            mapping[header] = {
                'target': target,
                'confidence': 1.0 if target else 0,
            }
    else:
        mapping = infer_mapping(headers)
        mapping = _resolve_mapping_conflicts(mapping)

    # 检测来源
    source = detect_source(headers, filename)

    # 获取已有数据用于值标准化
    existing = {}
    for field in ('account', 'category', 'subcategory', 'merchant', 'member', 'project'):
        existing[field] = get_existing_values(field)
    synonyms = load_synonyms()

    # 转换前5行做预览
    preview_rows = []
    for row in rows[:5]:
        converted, extra = _convert_row(row, mapping, existing, synonyms)
        preview_rows.append(converted)

    # 统计未映射列
    unmapped = [h for h, info in mapping.items() if not info.get('target')]

    # 标签建议
    sample_with_normalized = []
    for row in rows[:100]:
        converted, _ = _convert_row(row, mapping, existing, synonyms)
        row['_normalized'] = converted
        sample_with_normalized.append(row)
    suggested_tags = suggest_tags(source, sample_with_normalized)

    # 重复估算
    duplicate_estimate = _estimate_duplicates(rows, mapping, existing, synonyms)

    return {
        'detected_source': source,
        'encoding': encoding,
        'headers': headers,
        'mapping': mapping,
        'unmapped_columns': unmapped,
        'preview_rows': preview_rows,
        'total_rows': len(rows),
        'suggested_tags': suggested_tags,
        'duplicate_estimate': duplicate_estimate,
    }


def execute_import(file_bytes, mapping, tags=None, skip_duplicates=True,
                   filename='', batch_source=None):
    """
    执行导入

    参数:
        file_bytes: CSV 文件内容（bytes）
        mapping: 列映射 { csv列名: target_field }
        tags: 标签列表 ["微信导入", "2024-06"]
        skip_duplicates: 是否跳过重复记录
        filename: 原始文件名
        batch_source: 数据来源（不传则自动检测）

    返回:
    {
        "batch_id": 1,
        "imported": 125,
        "skipped": 3,
        "duplicates_found": 3,
        "tags_applied": [...],
        "errors": [...]
    }
    """
    # 解析 CSV
    headers, rows, encoding = parse_csv(file_bytes)
    if not rows:
        return {'error': 'CSV 文件为空', 'imported': 0}

    # 构建映射（用户提供的映射已经是最终的）
    full_mapping = {}
    for header in headers:
        target = mapping.get(header)
        full_mapping[header] = {
            'target': target,
            'confidence': 1.0 if target else 0,
        }

    # 检测来源
    if not batch_source:
        batch_source = detect_source(headers, filename)

    # 获取已有数据
    existing = {}
    for field in ('account', 'category', 'subcategory', 'merchant', 'member', 'project'):
        existing[field] = get_existing_values(field)
    synonyms = load_synonyms()

    # 转换所有行
    converted_rows = []
    errors = []
    for i, row in enumerate(rows):
        try:
            converted, extra = _convert_row(row, full_mapping, existing, synonyms)
            if converted:
                converted['_extra_data'] = extra if extra else None
                converted['_row_index'] = i
                converted_rows.append(converted)
        except Exception as e:
            errors.append(f'第 {i+1} 行: {str(e)}')

    # 从备注/extra_data 中提取 #xxx# 形式的自动标签
    for row in converted_rows:
        auto_tags = set()
        note = row.get('note', '') or ''
        extra = row.get('_extra_data', {}) or {}
        extra_text = ' '.join(str(v) for v in extra.values()) if isinstance(extra, dict) else ''
        for text in [note, extra_text]:
            for m in re.finditer(r'#([^#]+)#', text):
                tag = m.group(1).strip()
                if tag:
                    auto_tags.add(tag)
        row['_auto_tags'] = list(auto_tags)

    # 过滤无效行（缺少必填字段）
    valid_rows = []
    skipped = 0
    for row in converted_rows:
        if not row.get('type') or row.get('amount') is None or not row.get('date'):
            skipped += 1
            continue
        valid_rows.append(row)

    # 去重检测
    duplicates_found = 0
    final_rows = []
    if skip_duplicates:
        for row in valid_rows:
            dupes = _check_duplicate(row['type'], row['amount'],
                                     row.get('category', ''), row.get('account', ''),
                                     row['date'])
            if dupes:
                duplicates_found += 1
            else:
                final_rows.append(row)
    else:
        final_rows = valid_rows

    # 按日期排序
    final_rows.sort(key=lambda x: x['date'])

    # 写入数据库
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 创建导入批次记录
    mapping_json = json.dumps(mapping, ensure_ascii=False)
    tags_json = json.dumps(tags or [], ensure_ascii=False)
    c.execute('''INSERT INTO import_batches (source, filename, row_count, mapping, tags)
                 VALUES (?, ?, ?, ?, ?)''',
              (batch_source, filename, len(final_rows), mapping_json, tags_json))
    batch_id = c.lastrowid

    # 插入交易记录
    imported = 0
    for row in final_rows:
        extra_json = json.dumps(row['_extra_data'], ensure_ascii=False) if row.get('_extra_data') else None
        c.execute('''INSERT INTO transactions
            (type, amount, category, subcategory, account, project, member, merchant,
             note, trans_date, is_deleted, extra_data, batch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)''',
            (row['type'], row['amount'],
             row.get('category', ''), row.get('subcategory', ''),
             row.get('account', ''), row.get('project', ''),
             row.get('member', ''), row.get('merchant', ''),
             row.get('note', ''), row['date'],
             extra_json, batch_id))
        tx_id = c.lastrowid

        # 打标签
        if tags:
            for tag_name in tags:
                tag_name = tag_name.strip()
                if not tag_name:
                    continue
                # 确保标签存在
                c.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                tag_row = c.fetchone()
                if tag_row:
                    tag_id = tag_row[0]
                else:
                    c.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                    tag_id = c.lastrowid
                # 关联
                c.execute("INSERT OR IGNORE INTO transaction_tags (transaction_id, tag_id) VALUES (?, ?)",
                          (tx_id, tag_id))

        imported += 1

    conn.commit()
    conn.close()

    # 更新别名：把本次映射中用户确认的新值加入 synonyms
    _update_synonyms_from_mapping(mapping, rows, existing, synonyms)

    return {
        'batch_id': batch_id,
        'imported': imported,
        'skipped': skipped,
        'duplicates_found': duplicates_found,
        'tags_applied': tags or [],
        'auto_tags': sorted({tag for row in final_rows for tag in row.get('_auto_tags', [])}) if final_rows else [],
        'errors': errors[:20],  # 最多返回20个错误
    }


# ─── 内部辅助函数 ──────────────────────────────────────────

def _convert_row(row, mapping, existing, synonyms):
    """
    转换一行 CSV 数据为系统格式

    返回 (converted_dict, extra_dict)
    converted_dict: 系统字段 → 标准化后的值
    extra_dict: 未映射列的原始值（存入 extra_data）
    """
    converted = {}
    extra = {}

    for header, value in row.items():
        info = mapping.get(header, {})
        target = info.get('target')

        if not target:
            # 未映射列 → 存入 extra
            if value and str(value).strip():
                extra[header] = str(value).strip()
            continue

        value_str = str(value).strip() if value else ''

        if target == 'type':
            converted['type'] = normalize_type(value_str)
        elif target == 'amount':
            converted['amount'] = normalize_amount(value_str)
        elif target == 'date':
            converted['date'] = normalize_date(value_str)
        elif target in ('category', 'subcategory', 'account', 'merchant', 'member', 'project'):
            normalized, confidence, method = normalize_value(
                target, value_str,
                existing_values=existing.get(target, []),
                synonyms=synonyms
            )
            converted[target] = normalized
        elif target == 'note':
            converted['note'] = value_str

    return converted, extra if extra else None


def _check_duplicate(type_, amount, category, account, trans_date):
    """检查是否存在重复记录"""
    date_part = trans_date.split(' ')[0] if ' ' in trans_date else trans_date
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT id FROM transactions
                     WHERE is_deleted = 0 AND type = ? AND amount = ?
                       AND category = ?
                       AND strftime('%Y-%m-%d', trans_date) = ?''',
                  (type_, amount, category, date_part))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def _estimate_duplicates(rows, mapping, existing, synonyms):
    """估算重复记录数（采样前100条）"""
    count = 0
    sample = rows[:100]
    for row in sample:
        converted, _ = _convert_row(row, mapping, existing, synonyms)
        if not converted.get('type') or not converted.get('amount') or not converted.get('date'):
            continue
        dupes = _check_duplicate(
            converted['type'], converted['amount'],
            converted.get('category', ''), converted.get('account', ''),
            converted['date']
        )
        if dupes:
            count += 1
    # 按比例估算
    if sample:
        ratio = count / len(sample)
        return int(ratio * len(rows))
    return 0


def _update_synonyms_from_mapping(mapping, rows, existing, synonyms):
    """从导入结果中学习新的别名映射"""
    updated = False

    for header, info in mapping.items():
        # mapping 可能是 {header: target_str} 或 {header: {target, confidence}}
        if isinstance(info, dict):
            target = info.get('target')
        else:
            target = info

        if not target or target in ('type', 'amount', 'date', 'note'):
            continue

        # 收集这个列中的所有值
        values = set()
        for row in rows:
            val = str(row.get(header, '')).strip()
            if val:
                values.add(val)

        existing_vals = existing.get(target, [])

        for val in values:
            # 检查是否需要创建别名（值不在已有列表中，但被标准化到了某个已有值）
            normalized, confidence, method = normalize_value(
                target, val,
                existing_values=existing_vals,
                synonyms=synonyms
            )

            if method in ('synonym', 'synonym_partial', 'contains') and normalized != val:
                # 这是一个别名，记录下来
                if target not in synonyms:
                    synonyms[target] = {}
                if normalized not in synonyms[target]:
                    synonyms[target][normalized] = []
                if val not in synonyms[target][normalized]:
                    synonyms[target][normalized].append(val)
                    updated = True

    if updated:
        save_synonyms(synonyms)


# ─── 向后兼容 ──────────────────────────────────────────────

def import_csv_compat(csv_file):
    """
    向后兼容的导入函数（保持旧的 import_csv 签名）

    使用默认的随手记格式映射
    """
    if not os.path.exists(csv_file):
        print(f"❌ 文件不存在: {csv_file}")
        return False

    with open(csv_file, 'rb') as f:
        file_bytes = f.read()

    filename = os.path.basename(csv_file)

    # 默认映射（兼容旧格式）
    default_mapping = {
        '交易类型': 'type',
        '日期': 'date',
        '金额': 'amount',
        '类别': 'category',
        '子类别': 'subcategory',
        '账户': 'account',
        '项目': 'project',
        '成员': 'member',
        '商家': 'merchant',
        '备注': 'note',
    }

    # 先解析看有哪些列
    headers, rows, encoding = parse_csv(file_bytes)

    # 构建映射：优先用默认映射，其他列走推断
    mapping = {}
    for header in headers:
        if header in default_mapping:
            mapping[header] = default_mapping[header]
        else:
            inferred = infer_mapping([header])
            if inferred.get(header, {}).get('target'):
                mapping[header] = inferred[header]['target']

    result = execute_import(
        file_bytes=file_bytes,
        mapping=mapping,
        tags=None,
        skip_duplicates=False,
        filename=filename,
        batch_source='随手记'
    )

    if 'error' in result:
        print(f"❌ {result['error']}")
        return False

    print(f"✅ 导入完成: 成功 {result['imported']}, 跳过 {result['skipped']}, "
          f"重复 {result['duplicates_found']}")
    return True
