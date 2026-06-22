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
# 在容器内导入
docker exec -it ledger python scripts/import_ledger.py /data/wechat_bill_202606.csv
```

**Agent 回复**：
> ✅ 导入完成，共 152 条记录。建议说"学习记账"让我分析你的记账习惯。

---

### 场景二：导出6月食品支出

**用户说**：
> 把6月份食品酒水的记录导出

**Agent 执行**：
```bash
curl "$BASE_URL/api/export?format=csv&category=食品酒水&start_date=2026-06-01&end_date=2026-06-30"
```

---

### 场景三：分析记账习惯（学习）

**用户说**：
> 学习一下我的记账数据

**Agent 执行**：
```bash
curl $BASE_URL/api/analyze
```

**Agent 用 remember 保存关键模式**

---

### 场景四：导出全部数据

**用户说**：
> 帮我导出所有流水

**Agent 执行**：
```bash
curl "$BASE_URL/api/export?format=json&start_date=2026-01-01&end_date=2026-12-31"
```
