"""
交易类型系统

设计目标：
- 兼容现有 `收入/支出` 为主线的统计与展示
- 支持样本数据里的 `转入/转出/余额变更/负债变更/债权变更`
- 支持对账/修正用的 `调整` 类型
- 不硬编码把 `转入/转出` 当成 `收入/支出`
"""

# ── 规范类型 ──────────────────────────────────────────────

INCOME = '收入'
EXPENSE = '支出'
TRANSFER = '转账'
BALANCE_ADJUST = '余额变更'
LIABILITY_CHANGE = '负债变更'
CLAIMS_CHANGE = '债权变更'
RECONCILIATION = '调整'

TYPE_CHOICES = [
    INCOME,
    EXPENSE,
    TRANSFER,
    BALANCE_ADJUST,
    LIABILITY_CHANGE,
    CLAIMS_CHANGE,
    RECONCILIATION,
]

# 前端默认展示顺序
TYPE_ORDER = [
    INCOME,
    EXPENSE,
    TRANSFER,
    BALANCE_ADJUST,
    LIABILITY_CHANGE,
    CLAIMS_CHANGE,
    RECONCILIATION,
]

# ── 别名映射 ──────────────────────────────────────────────

TYPE_ALIASES = {
    # 收入类
    INCOME: ['收入', 'income', '收款', '卖水收入', '退保', '意外来钱', '房租押金', '报销'],
    # 支出类
    EXPENSE: ['支出', 'expense', '消费', '付款', '退款'],
    # 转账类
    TRANSFER: ['转账', 'transfer', '转入', '转出', '还信用卡', '代付'],
    # 余额变更
    BALANCE_ADJUST: ['余额变更', 'balance', '余额调整'],
    # 负债变更
    LIABILITY_CHANGE: ['负债变更', 'liability', '负债调整', '信用卡'],
    # 债权变更
    CLAIMS_CHANGE: ['债权变更', 'claims', '债权调整', '收债'],
    # 对账调整
    RECONCILIATION: ['调整', 'reconciliation', '对账', '修正'],
}

# ── 统计分组 ──────────────────────────────────────────────

STAT_INCOME_TYPES = {INCOME}
STAT_EXPENSE_TYPES = {EXPENSE}
STAT_TRANSFER_TYPES = {TRANSFER}
STAT_BALANCE_SHEET_TYPES = {BALANCE_ADJUST, LIABILITY_CHANGE, CLAIMS_CHANGE}
STAT_EXCLUDE_TYPES = STAT_TRANSFER_TYPES | STAT_BALANCE_SHEET_TYPES | {RECONCILIATION}


def is_stat_income(type_):
    return type_ in STAT_INCOME_TYPES


def is_stat_expense(type_):
    return type_ in STAT_EXPENSE_TYPES


def is_transfer(type_):
    return type_ in STAT_TRANSFER_TYPES


def is_balance_sheet(type_):
    return type_ in STAT_BALANCE_SHEET_TYPES


def is_excluded_from_income_expense(type_):
    return type_ in STAT_EXCLUDE_TYPES


# ── 兼容映射 ──────────────────────────────────────────────

LEGACY_TYPE_MAP = {
    '转入': TRANSFER,
    '转出': TRANSFER,
    '余额变更': BALANCE_ADJUST,
    '负债变更': LIABILITY_CHANGE,
    '债权变更': CLAIMS_CHANGE,
}


def _match_alias(raw):
    if not raw:
        return None
    raw_clean = str(raw).strip()
    # 精确匹配优先，避免 `调整` 被更长的别名如 `余额调整` 误匹配
    for canonical, aliases in TYPE_ALIASES.items():
        for alias in aliases:
            if raw_clean == alias:
                return canonical
    # 次级：包含匹配（用于 `卖水收入` -> `收入` 这类情况）
    for canonical, aliases in TYPE_ALIASES.items():
        for alias in aliases:
            if alias in raw_clean or raw_clean in alias:
                return canonical
    return None


def normalize_raw_type(raw_value):
    """按别名映射将原始文本标准化为规范类型"""
    if not raw_value:
        return None
    raw_clean = str(raw_value).strip()
    if not raw_clean:
        return None

    matched = _match_alias(raw_clean)
    if matched:
        return matched

    return None
