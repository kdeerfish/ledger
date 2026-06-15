# 通用记录模板 - 日常操作示例

与 `references/template.md` 对应，展示模板创建和使用的完整对话。

---

### 场景一：创建零食模板

**用户说**：
> 帮我创建一个零食模板，拼多多买零食一般6块左右

**Agent 执行**（`template_type`=模板类型，`type`=交易类型，此处一致均为支出）：
```bash
python3 scripts/ledger_cli.py template_create '{"name":"零食","template_type":"支出","type":"支出","amount":6,"category":"食品酒水","subcategory":"零食","account":"储蓄卡","merchant":"拼多多"}'
```

**Agent 回复**：
> ✅ 已创建模板"零食"（ID:1）：拼多多买零食 6 元（储蓄卡）

---

### 场景二：创建午餐模板

**用户说**：
> 记个午餐模板，一般25块，微信零钱付

**Agent 执行**（`template_type`=模板类型，`type`=交易类型，此处一致均为支出）：
```bash
python3 scripts/ledger_cli.py template_create '{"name":"午餐","template_type":"支出","type":"支出","amount":25,"category":"食品酒水","subcategory":"早午晚餐","account":"微信零钱","merchant":"食堂"}'
```

**Agent 回复**：
> ✅ 已创建模板"午餐"（ID:2）：食堂午餐 25 元（微信零钱）

---

### 场景三：创建工资模板

**用户说**：
> 做个工资模板，工资5000，招商银行

**Agent 执行**（`template_type`=收入型模板，`type`=收入交易）：
```bash
python3 scripts/ledger_cli.py template_create '{"name":"工资","template_type":"收入","type":"收入","amount":5000,"category":"职业收入","account":"招商银行","note":"月薪"}'
```

**Agent 回复**：
> ✅ 已创建模板"工资"（ID:3）：工资收入 5000 元（招商银行）

---

### 场景四：用模板快速记账

**用户说**：
> 用零食模板记一笔

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py template_list '{"template_type":"支出"}'
```

**输出**：
```
ID:1  零食  支出  6.00  食品酒水/零食  储蓄卡  拼多多
ID:2  午餐  支出  25.00  食品酒水/早午晚餐  微信零钱  食堂
```

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py template_apply '{"id":1}'
```

**Agent 回复**：
> ✅ 已记录：拼多多买零食 6 元（储蓄卡）

---

### 场景五：模板记但改金额

**用户说**：
> 用午餐模板记一笔，但今天吃了35

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py template_apply '{"id":2,"amount":35}'
```

**Agent 回复**：
> ✅ 已记录：食堂午餐 35 元（微信零钱）

---

### 场景六：让系统推荐模板

**用户说**：
> 看看有什么常用模板推荐

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py template_suggest '{"limit":5}'
```

**输出示例**：
```
推荐模板：
1. 零食 - 食品酒水 6元（最近使用3次）
2. 午餐 - 食品酒水 25元（最近使用8次）
3. 工资 - 职业收入 5000元（每月使用）
```

---

### 场景七：更新模板金额

**用户说**：
> 零食涨价了，模板改成8块

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py template_update '{"id":1,"amount":8}'
```

**Agent 回复**：
> ✅ 已更新模板"零食"：金额 6 → 8 元

---

### 场景八：删除模板

**用户说**：
> 把零食模板删掉，不用了

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py template_delete '{"id":1}'
```

**Agent 回复**：
> ✅ 已删除模板"零食"
