# 智能导入 + 增强导出 实施计划

> 分支: `feature/smart-import-export`

---

## 一、整体改动范围

### 影响面总览

```
新增文件（8个）：
  ledger_modules/import_engine.py      ← 智能导入核心引擎
  ledger_modules/export_engine.py      ← 增强导出引擎
  web/routes/import_api.py             ← 导入 API 端点
  web/routes/export_api.py             ← 导出 API 端点
  frontend/src/pages/Import.jsx        ← 导入页面
  frontend/src/pages/Export.jsx        ← 导出页面
  tests/test_import_engine.py          ← 导入引擎测试
  tests/test_export_engine.py          ← 导出引擎测试

修改文件（6个）：
  ledger_modules/db.py                 ← 数据库迁移 v2→v3
  ledger_modules/transactions.py       ← 重构 import_csv + export 兼容
  web/app.py                           ← 注册新蓝图 + 依赖检查
  frontend/src/App.jsx                 ← 加路由
  frontend/src/components/Layout.jsx   ← 导航栏加入口
  frontend/src/api/index.js            ← API 客户端函数

新增依赖：
  requirements.txt                     ← +openpyxl, +reportlab, +chardet

不改的：
  ❌ 用户体系
  ❌ 现有维度表结构（保持纯文本）
  ❌ 标签表结构（已够用）
  ❌ 预算/模板表结构
  ❌ 现有 API 行为（保持兼容）
```

---

## 二、分步实施

### Phase 1: 数据库迁移 v2→v3

**文件:** `ledger_modules/db.py`

**改动内容：**
- `DB_VERSION = 3`
- 新建 `import_batches` 表
- `transactions` 加 `extra_data TEXT` 和 `batch_id INTEGER`
- 补索引 `idx_trans_merchant`, `idx_trans_account`

```sql
CREATE TABLE IF NOT EXISTS import_batches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    filename    TEXT,
    row_count   INTEGER DEFAULT 0,
    mapping     TEXT,
    tags        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

ALTER TABLE transactions ADD COLUMN extra_data TEXT;
ALTER TABLE transactions ADD COLUMN batch_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_trans_merchant ON transactions(merchant);
CREATE INDEX IF NOT EXISTS idx_trans_account ON transactions(account);
```

**风险:** ⭐ 低

---

### Phase 2: 导入引擎

**新增文件:** `ledger_modules/import_engine.py`

**核心功能：**
- CSV 编码检测（UTF-8/GBK/GB2312）
- 列名语义推断（内置模式匹配表）
- 值标准化（基于 analyze_data() 的现有数据）
- 别名配置管理（存在 meta 表 key='synonyms'）
- 预览模式 + 执行模式
- extra_data 存储兜底

**核心函数：**
```python
detect_encoding(file_bytes) -> str
parse_csv_headers(file_bytes) -> (headers, encoding)
infer_mapping(headers, sample_rows) -> dict
load_synonyms() -> dict
save_synonyms(synonyms: dict)
normalize_value(field, raw_value, existing_values) -> str
preview_import(file_bytes, user_mapping=None) -> dict
execute_import(file_bytes, mapping, tags, skip_duplicates=True) -> dict
```

**列名推断内置模式：**
```
type      ← 交易类型/类型/收/支/收支类型
amount    ← 金额/支付金额/交易金额/金额(元)
date      ← 日期/交易时间/交易日期/记账时间
category  ← 类别/分类/交易分类
account   ← 账户/支付方式/资金渠道/付款方式
merchant  ← 商家/交易对方/对方/商户/交易商户
member    ← 成员/交易人
project   ← 项目
note      ← 备注/商品说明/商品名称/交易说明
```

**标签推断：**
- 来源标签：从文件名特征 / CSV列名特征推断
- 时间标签：根据数据日期范围生成

**风险:** ⚠️ 中（核心逻辑，需充分测试）

---

### Phase 3: 导入 API

**新增文件:** `web/routes/import_api.py`

**端点：**
```
POST /api/import/preview   → 上传CSV，返回映射建议+预览数据
POST /api/import/execute   → 确认后执行导入
```

**修改:** `web/app.py` 注册蓝图

**风险:** ⭐ 低

---

### Phase 4: 导出引擎

**新增文件:** `ledger_modules/export_engine.py`

**核心功能：**
- Excel 多 Sheet（明细+月度汇总+分类统计+账户统计）
- PDF 月度报告（表格+图表）
- CSV 修复兼容性（列名与导入一致）
- JSON 保持现有格式
- 导出包含 extra_data 和标签

**核心函数：**
```python
get_export_data(filters) -> dict
export_excel(data, output, sheets) -> str
export_pdf(data, output, title) -> str
export_csv(data, output, import_compatible) -> str
export_json(data, output) -> str
```

**新增依赖:** `openpyxl`, `reportlab`

**风险:** ⭐ 低

---

### Phase 5: 导出 API

**新增文件:** `web/routes/export_api.py`

**端点：**
```
GET /api/export/preview  → 返回记录数
GET /api/export          → 文件流下载（Excel/CSV/PDF/JSON）
```

**修改:** `web/app.py` 注册蓝图

**风险:** ⭐ 低

---

### Phase 6: 前端导入页面

**新增文件:** `frontend/src/pages/Import.jsx`

**4步向导：**
1. 上传文件（拖拽+点击）
2. 确认映射（表格展示，下拉可改）
3. 设置标签（复用TagSelector）
4. 确认导入（汇总+重复警告+执行）

**修改:**
- `App.jsx` 加 `/import` 路由
- `Layout.jsx` 导航栏加"导入"
- `api/index.js` 加两个函数

---

### Phase 7: 前端导出页面

**新增文件:** `frontend/src/pages/Export.jsx`

**页面：**
- 时间范围+筛选条件选择
- 四个格式卡片（Excel/CSV/PDF/JSON）
- 内容选项（明细/汇总/统计）
- 预览记录数+下载

**修改:**
- `App.jsx` 加 `/export` 路由
- `Layout.jsx` 导航栏加"导出"
- `api/index.js` 加两个函数

---

### Phase 8: 向后兼容

**修改:** `ledger_modules/transactions.py`
- `import_csv()` 保留旧签名，内部转调 import_engine
- `export_transactions()` 内部转调 export_engine

**修改:** `scripts/cli.py`
- export 命令加 `--format excel/pdf` 选项

---

### Phase 9: 测试

**新增:**
- `tests/test_import_engine.py` — 编码检测、列名推断、标准化、导入执行、去重、extra_data、标签
- `tests/test_export_engine.py` — Excel/PDF/CSV/JSON生成、筛选、extra_data导出

---

## 三、实施顺序

```
Phase 1 数据库迁移 ──→ Phase 2 导入引擎 ──→ Phase 3 导入API ──→ Phase 6 前端导入
                    ╲                                              ╱
                     ╲→ Phase 4 导出引擎 → Phase 5 导出API → Phase 7 前端导出
Phase 8 向后兼容 ← 依赖 Phase 2 + 4
Phase 9 测试 ← 贯穿全程
```

## 四、风险矩阵

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 列名推断错误 | 中 | 预览确认机制，用户可修改映射 |
| CSV编码检测不准 | 低 | 自动检测+手动选择兜底 |
| 文件上传安全 | 中 | 限大小10MB、行数50000、只接受CSV |
| Excel/PDF库兼容 | 低 | openpyxl+reportlab都是成熟库 |
| 现有CLI兼容 | 低 | 旧函数保留wrapper |
| 大文件前端卡顿 | 低 | 预览只传表头+前5行 |
