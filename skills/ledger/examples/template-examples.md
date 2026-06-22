# 模板管理 - 日常操作示例

与 `references/template.md` 对应，展示模板创建和使用的完整对话。

---

### 场景一：创建零食模板

**用户说**：
> 帮我创建一个零食模板，拼多多买零食一般6块左右

**Agent 执行**：
```bash
curl -X POST $BASE_URL/api/templates \
  -H 'Content-Type: application/json' \
  -d '{"name":"零食","template_type":"支出","type":"支出","amount":6,"category":"食品酒水","subcategory":"零食","account":"储蓄卡","merchant":"拼多多"}'
```

**Agent 回复**：
> ✅ 已创建模板"零食"（ID:1）：拼多多买零食 6 元（储蓄卡）

---

### 场景二：创建午餐模板

**用户说**：
> 记个午餐模板，一般25块，微信零钱付

**Agent 执行**：
```bash
curl -X POST $BASE_URL/api/templates \
  -H 'Content-Type: application/json' \
  -d '{"name":"午餐","template_type":"支出","type":"支出","amount":25,"category":"食品酒水","subcategory":"早午晚餐","account":"微信零钱","merchant":"食堂"}'
```

---

### 场景三：创建工资模板

**用户说**：
> 做个工资模板，工资5000，招商银行

**Agent 执行**：
```bash
curl -X POST $BASE_URL/api/templates \
  -H 'Content-Type: application/json' \
  -d '{"name":"工资","template_type":"收入","type":"收入","amount":5000,"category":"职业收入","account":"招商银行","note":"月薪"}'
```

---

### 场景四：查看模板列表

**用户说**：
> 帮我看看有哪些模板

**Agent 执行**：
```bash
curl $BASE_URL/api/templates
```

---

### 场景五：使用模板

**用户说**：
> 用零食模板记一笔

**Agent 执行**：
```bash
curl -X POST $BASE_URL/api/templates/1/use
```

---

### 场景六：更新模板金额

**用户说**：
> 零食涨价了，模板改成8块

**Agent 执行**：
```bash
curl -X PUT $BASE_URL/api/templates/1 \
  -H 'Content-Type: application/json' \
  -d '{"amount":8}'
```

---

### 场景七：删除模板

**用户说**：
> 把零食模板删掉，不用了

**Agent 执行**：
```bash
curl -X DELETE $BASE_URL/api/templates/1
```
