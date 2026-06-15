# 基础命令 - 日常操作示例

与 `references/basic.md` 对应，展示日常记账查账的完整对话。

---

### 场景一：拼多多买零食

**用户说**：
> 记一笔，拼多多买了6块8的零食

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py add '{"type":"支出","amount":6.8,"category":"食品酒水","subcategory":"零食","account":"储蓄卡","merchant":"拼多多"}'
```

**Agent 回复**：
> ✅ 已记录：拼多多买零食 6.80 元（储蓄卡）

---

### 场景二：滴滴打车

**用户说**：
> 今天打车花了20块

**Agent 分析**：之前已学习过用户习惯，知道打车常用滴滴、默认微信零钱。

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py add '{"type":"支出","amount":20,"category":"行车交通","subcategory":"打车租车","account":"微信零钱","merchant":"滴滴"}'
```

**Agent 回复**：
> ✅ 已记录：滴滴打车 20.00 元（微信零钱）

---

### 场景三：收到工资

**用户说**：
> 记一笔收入，工资5000到招商银行

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py add '{"type":"收入","amount":5000,"category":"职业收入","account":"招商银行","note":"6月工资"}'
```

**Agent 回复**：
> ✅ 已记录：工资收入 5000.00 元（招商银行）

---

### 场景四：看看这个月花了多少

**用户说**：
> 查一下这个月的支出情况

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py summary '{"year":2026,"month":6}'
```

**输出示例**：
```
本月收入：15000.00 元
本月支出：3560.50 元
结余：11439.50 元
```

---

### 场景五：搜搜在拼多多花了多少钱

**用户说**：
> 查查我在拼多多买了什么

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py search '{"keyword":"拼多多","search_type":"merchant","limit":30}'
```

---

### 场景六：看食品酒水花了多少

**用户说**：
> 看看我6月份在吃的上面花了多少钱

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py filter '{"category":"食品酒水","start_date":"2026-06-01","end_date":"2026-06-30"}'
python3 scripts/ledger_cli.py stats '{"year":2026,"month":6,"group_by":"category"}'
```

### 场景七：查看最近的记录

**用户说**：
> 看看最近记的账

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py list '{"limit":10}'
```

**输出示例**：
```
ID:890  2026/06/15  支出   6.80  食品酒水/零食    储蓄卡  拼多多
ID:889  2026/06/15  支出  20.00  行车交通/打车租车  微信零钱  滴滴
ID:888  2026/06/14  收入  5000.00  职业收入      招商银行
...
```

> 💡 还有 `accounts`、`categories`、`members` 命令用于查看元数据列表，用法类似无参数即可。
