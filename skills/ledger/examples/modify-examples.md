# 修改命令 - 日常操作示例

与 `references/modify.md` 对应，展示修改、删除、恢复记录的完整对话。

---

### 场景一：改金额

**用户说**：
> 刚才那笔零食记错了，不是6块8是8块6

**Agent 执行**（先搜索找到记录）：
```bash
curl "http://127.0.0.1:5800/api/transactions/search?keyword=零食&search_type=category&limit=10"
```

**Agent 询问**：
> 请问是最近那笔 6.80 的零食吗？（ID:456）

**用户说**：
> 对

**Agent 执行**：
```bash
curl -X PUT http://127.0.0.1:5800/api/transactions/456 \
  -H 'Content-Type: application/json' \
  -d '{"field":"amount","value":8.6}'
```

---

### 场景二：改类别

**用户说**：
> 那笔拼多多买的应该是居家物业，不是食品酒水

**Agent 执行**：
```bash
curl "http://127.0.0.1:5800/api/transactions/search?keyword=拼多多&search_type=merchant&limit=10"
```

**Agent 询问**：
> 是 ID:789 这笔 11.50 元的拼多多记录吗？

**用户说**：
> 对

**Agent 执行**：
```bash
curl -X PUT http://127.0.0.1:5800/api/transactions/789 \
  -H 'Content-Type: application/json' \
  -d '{"category":"居家物业","subcategory":"日常用品"}'
```

---

### 场景三：改商家

**用户说**：
> 那笔车费是滴滴不是美团，帮我改一下

**Agent 执行**：
```bash
curl "http://127.0.0.1:5800/api/transactions/search?keyword=打车&search_type=note&limit=20"
```

**Agent 询问**：
> 找到几条打车记录，请问是哪一笔？

**用户说**：
> 就昨天20块那个

**Agent 执行**（假设ID是321）：
```bash
curl -X PUT http://127.0.0.1:5800/api/transactions/321 \
  -H 'Content-Type: application/json' \
  -d '{"merchant":"滴滴"}'
```

---

### 场景四：删掉重复的记录

**用户说**：
> 刚才不小心记重了，帮我删掉多余的那条

**Agent 执行**：
```bash
curl "http://127.0.0.1:5800/api/transactions?limit=20"
```

**Agent 询问**：
> 最近记录中有两笔相同的，要删掉哪一条？请提供 ID

**用户说**：
> 删掉 ID 654

**Agent 执行**：
```bash
curl -X DELETE http://127.0.0.1:5800/api/transactions/654
```

---

### 场景五：恢复误删的记录

**用户说**：
> 刚才删错了，帮我恢复一下

**Agent 执行**（查看已删除记录）：
```bash
curl "http://127.0.0.1:5800/api/transactions?limit=20&include_deleted=true"
```

**Agent 询问**：
> 找到一条已删除的记录（ID:654），要恢复它吗？

**用户说**：
> 对

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions/654/restore
```
