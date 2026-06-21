# 字段用途 - 从真实数据看字段区分

与 `references/field-guide.md` 对应，用对话形式展示各字段的正确填法。

> ⚠️ 以下金额均为用户说出的，agent 不能自行编造金额。
> agent 要根据 field-guide.md 的字段定义，正确区分 account/merchant/category/subcategory/project/member。

---

### 场景一：拼多多买零食

**用户说**：
> 拼多多买了零食，6块8

**Agent 分析**：
- `merchant`：拼多多（消费平台）
- `category`：食品酒水（花在吃上）
- `subcategory`：零食
- `project`：日常支出
- `member`：本人
- `account`：根据用户习惯 → 储蓄卡（默认使用，用户可更改）

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":6.8,"category":"食品酒水","subcategory":"零食","account":"储蓄卡","merchant":"拼多多","project":"日常支出","member":"本人"}'
```

---

### 场景二：滴滴打车

**用户说**：
> 打车花了20块

**Agent 分析**：
- 打车 → `category`：行车交通，`subcategory`：打车租车
- 没说商家 → **必须询问**
- 没说账户 → **必须询问**

**Agent 询问**：
> 用哪个平台打的车？（如滴滴、美团）用哪个账户支付？

**用户说**：
> 滴滴，微信零钱

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":20,"category":"行车交通","subcategory":"打车租车","account":"微信零钱","merchant":"滴滴","project":"日常支出","member":"本人"}'
```

---

### 场景三：拼多多买日用品

**用户说**：
> 拼多多买了些日用品，11块5

**Agent 分析**：
- `merchant`：拼多多
- 日用品 → `category`：居家物业，`subcategory`：日常用品
- 没说账户 → **必须询问**

**Agent 询问**：
> 用哪个账户支付？

**用户说**：
> 信用卡

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":11.5,"category":"居家物业","subcategory":"日常用品","account":"信用卡","merchant":"拼多多","project":"家庭支出","member":"家庭公用"}'
```

---

### 场景四：抖音买甜品

**用户说**：
> 抖音买了4块钱的甜品

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":4,"category":"食品酒水","subcategory":"甜品","account":"微信零钱","merchant":"抖音","project":"日常支出","member":"本人"}'
```

---

### 场景五：交社保

**用户说**：
> 帮我记一下交社保，538块6

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":538.6,"category":"金融保险","subcategory":"保险","account":"储蓄卡","member":"本人","note":"社保缴费"}'
```

---

### 场景六：充AI服务

**用户说**：
> 给DeepSeek充10块钱

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":10,"category":"自由职业","subcategory":"大模型费用","account":"储蓄卡","merchant":"AI平台","project":"AI项目","member":"本人","note":"AI服务充值"}'
```

---

### 场景七：工资到账

**用户说**：
> 工资到账5000

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"收入","amount":5000,"category":"职业收入","account":"招商银行","member":"本人","note":"月薪"}'
```

---

### 场景八：交水电费

**用户说**：
> 交水电费200

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":200,"category":"居家物业","subcategory":"房租水电","account":"储蓄卡","project":"固定支出","member":"家庭公用","note":"水电费"}'
```

---

### 场景九：转账给家人

**用户说**：
> 给家里转了1000

**Agent 执行**：
```bash
curl -X POST http://127.0.0.1:5800/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"type":"支出","amount":1000,"category":"其他杂项","subcategory":"礼尚往来","account":"微信零钱","member":"本人","note":"给家里"}'
```

---

## 关键原则（agent 必须遵守）

| 原则 | 说明 |
|------|------|
| **金额必须用户说** | agent 不能自己编造金额，用户没说就问 |
| **账户要问** | 用户没说用哪个账户时，必须询问 |
| **商家要问** | 用户只说"打车"没说是滴滴还是美团时，必须询问 |
| **字段要分清楚** | 拼多多是 merchant，不是 account 也不是 project |
| **依据习惯默认** | 如果用户习惯很清楚（如总是微信零钱付），可以默认并告知用户 |
