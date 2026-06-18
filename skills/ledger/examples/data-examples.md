# 数据命令 - 日常操作示例

与 `references/data.md` 对应，展示导入导出和数据分析的完整对话。

---

### 场景一：导入银行账单

**用户说**：
> 帮我导入这个月的微信账单

**Agent 回复**：
> 请提供 CSV 文件路径。Ledger 运行在 Docker 中，需要把文件放到 NAS 上后用容器内命令导入。

**用户说**：
> /volume1/docker/ledger/data/wechat_bill_202606.csv

**Agent 回复**：
> 请先把文件放到 `/volume1/docker/ledger/data/` 目录，然后执行：

```bash
# 先把文件放到数据目录
cp /path/to/export.csv /volume1/docker/ledger/data/
# 在容器内导入
docker exec -it ledger python scripts/import_ledger.py /data/wechat_bill_202606.csv
```

**输出**：
```
✅ 导入完成: 总行 156, 成功 152, 跳过 4
```

**Agent 回复**：
> ✅ 导入完成，共 152 条记录。建议说"学习"让我分析你的记账习惯。

---

### 场景二：导出6月食品支出

**用户说**：
> 把6月份食品酒水的记录导出成Excel

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py export '{"output":"june_food.csv","format":"csv","category":"食品酒水","start_date":"2026-06-01","end_date":"2026-06-30"}'
```

**Agent 回复**：
> ✅ 已导出到 june_food.csv

---

### 场景三：分析记账习惯（学习）

**用户说**：
> 学习一下我的记账数据

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py analyze '{}'
```

**输出**：
```
【账户】储蓄卡(256笔)、微信零钱(180笔)、信用卡(95笔)
【商家】拼多多(120笔)、滴滴(45笔)、美团(38笔)
【类别】食品酒水(320笔)、居家物业(150笔)、行车交通(80笔)
【成员】本人(400笔)、家庭公用(100笔)、fish(30笔)
```

**Agent 用 remember 保存关键模式**

**Agent 回复**：
> ✅ 已学习完成！我已记住你的常用账户、商家和类别习惯，后续记账会更准确。

---

### 场景四：导出数据

**用户说**：
> 帮我导出所有流水

**Agent 执行**：
```bash
python3 scripts/ledger_cli.py export '{"format":"csv","start_date":"2026-01-01","end_date":"2026-12-31"}'
```

**Agent 回复**：
> 数据已从 API 获取，请手动保存到文件。

