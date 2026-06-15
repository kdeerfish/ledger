# 修改命令 - 日常操作示例

与 `references/modify.md` 对应，展示修改、删除、恢复记录的完整对话。

---

### 场景一：改金额

**用户说**：
> 刚才那笔零食记错了，不是6块8是8块6

**Agent 分析**：需要先找到那笔记录。

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py search '{"keyword":"零食","search_type":"category","limit":10}'
```

**输出**：
```
ID:456  2026/06/15  支出  6.80  食品酒水/零食  储蓄卡  拼多多
ID:789  2026/06/14  支出  12.00  食品酒水/零食  微信零钱  拼多多
```

**Agent 询问**：
> 请问是最近那笔 6.80 的零食吗？（ID:456）

**用户说**：
> 对

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py update '{"id":456,"field":"amount","value":8.6}'
```

**Agent 回复**：
> ✅ 已更新：零食金额 6.80 → 8.60 元

---

### 场景二：改类别

**用户说**：
> 那笔拼多多买的应该是居家物业，不是食品酒水

**Agent 分析**：拼多多买的居家物业类商品，需要找到记录。

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py search '{"keyword":"拼多多","search_type":"merchant","limit":10}'
```

**输出**：
```
ID:789  2026/06/14  支出  11.50  食品酒水/零食  信用卡  拼多多
```

**Agent 询问**：
> 是 ID:789 这笔 11.50 元的拼多多记录吗？

**用户说**：
> 对

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py update '{"id":789,"field":"category","value":"居家物业"}'
python3 scripts/ledger_cli.py update '{"id":789,"field":"subcategory","value":"日常用品"}'
```

**Agent 回复**：
> ✅ 已更新：类别改为居家物业/日常用品

---

### 场景三：改商家

**用户说**：
> 那笔车费是滴滴不是美团，帮我改一下

**Agent 分析**：先搜索打车相关记录。

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py search '{"keyword":"打车","search_type":"note","limit":20}'
```

**Agent 询问**：
> 找到几条打车记录，请问是哪一笔？（描述一下金额或日期）

**用户说**：
> 就昨天20块那个

**Agent 执行**（假设ID是321）：
```bash
python3 scripts/ledger_cli.py update '{"id":321,"field":"merchant","value":"滴滴"}'
```

**Agent 回复**：
> ✅ 已更新：商家改为滴滴

---

### 场景四：删掉重复的记录

**用户说**：
> 刚才不小心记重了，帮我删掉多余的那条

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py list '{"limit":20}'
```

**Agent 询问**：
> 最近记录中有两笔相同的（都是零食 6.80 元），要删掉哪一条？请提供 ID

**用户说**：
> 删掉 ID 654

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py delete '{"id":654}'
```

**Agent 回复**：
> ✅ 已删除 ID:654（软删除，可说"恢复"来撤销）

---

### 场景五：恢复误删的记录

**用户说**：
> 刚才删错了，帮我恢复一下

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py list '{"limit":20,"include_deleted":true}'
```

**Agent 询问**：
> 找到一条已删除的记录（ID:654），要恢复它吗？

**用户说**：
> 对

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py restore '{"id":654}'
```

**Agent 回复**：
> ✅ 已恢复 ID:654
