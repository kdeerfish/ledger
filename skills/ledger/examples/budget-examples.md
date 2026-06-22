# 预算命令 - 日常操作示例

与 `references/budget.md` 对应，展示预算设置和管理的完整对话。

---

### 场景一：设置月度预算

**用户说**：
> 给食品酒水设个预算，每月1000块

**Agent 执行**：
```bash
curl -X POST $BASE_URL/api/budgets \
  -H 'Content-Type: application/json' \
  -d '{"category":"食品酒水","amount":1000}'
```

**Agent 回复**：
> ✅ 已设置食品酒水预算：1000 元/月

---

### 场景二：按账户设置预算

**用户说**：
> 信用卡这个月吃饭预算500

**Agent 执行**：
```bash
curl -X POST $BASE_URL/api/budgets \
  -H 'Content-Type: application/json' \
  -d '{"category":"餐饮","amount":500,"dimension_type":"account","dimension_value":"信用卡","year":2026,"month":6}'
```

**Agent 回复**：
> ✅ 已设置信用卡的餐饮预算：500 元（2026年6月）

---

### 场景三：查看6月预算执行情况

**用户说**：
> 看看这个月预算花超了没

**Agent 执行**：
```bash
curl "$BASE_URL/api/budgets/check?year=2026&month=6"
```

---

### 场景四：查看预算列表

**用户说**：
> 看看这个月有哪些预算

**Agent 执行**：
```bash
curl "$BASE_URL/api/budgets?year=2026&month=6"
```
