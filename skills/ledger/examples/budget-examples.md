# 预算命令 - 日常操作示例

与 `references/budget.md` 对应，展示预算设置和管理的完整对话。

---

### 场景一：设置月度预算

**用户说**：
> 给食品酒水设个预算，每月1000块

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py budget_set '{"category":"食品酒水","amount":1000}'
```

**Agent 回复**：
> ✅ 已设置食品酒水预算：1000 元/月

---

### 场景二：按账户设置预算

**用户说**：
> 信用卡这个月吃饭预算500

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py budget_set '{"category":"餐饮","amount":500,"dimension_type":"account","dimension_value":"信用卡","year":2026,"month":6}'
```

**Agent 回复**：
> ✅ 已设置信用卡的餐饮预算：500 元（2026年6月）

---

### 场景三：查看6月预算执行情况

**用户说**：
> 看看这个月预算花超了没

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py budget_check '{"year":2026,"month":6}'
```

**输出示例**：
```
食品酒水：预算 1000，已花 680，剩余 320
餐饮（信用卡）：预算 500，已花 420，剩余 80
```

---

### 场景四：用模板快速设置预算

**用户说**：
> 把上个月的吃饭预算模板套用到这个月

**Agent 执行**：
```bash
# 1. 先推荐常用模板
python3 scripts/ledger_cli.py budget_template_suggest '{"limit":3}'
```

**输出**：
```
推荐模板：
1. 吃饭模板 - 餐饮 400元/月 (信用卡)
2. 零食模板 - 食品酒水 200元/月
3. 交通模板 - 行车交通 300元/月
```

**Agent 执行**：
```bash
# 2. 应用"吃饭模板"（假设ID=2）到7月
python3 scripts/ledger_cli.py budget_template_apply '{"id":2,"year":2026,"month":7}'
```

**Agent 回复**：
> ✅ 已为7月套用"吃饭模板"：信用卡餐饮预算 400 元

---

### 场景五：创建预算模板

**用户说**：
> 创建一个吃饭预算模板，餐饮每个月400

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py budget_template_create '{"name":"吃饭模板","description":"日常吃饭","category":"餐饮","amount":400,"dimension_type":"account","dimension_value":"信用卡"}'
```

**Agent 回复**：
> ✅ 已创建预算模板"吃饭模板"：信用卡餐饮 400 元/月

---

### 场景六：删除预算模板

**用户说**：
> 把吃饭模板删掉

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py budget_template_delete '{"id":1}'
```

**Agent 回复**：
> ✅ 已删除预算模板 ID:1
