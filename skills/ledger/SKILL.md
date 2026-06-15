---
name: ledger
description: 记账、查账、统计、预算、导入导出、学习用户习惯等个人财务管理 CLI 工具
version: 1.3.0
---

# Ledger - 个人记账系统

## 核心概念

这是个人记账系统的 AI Agent 技能，通过 CLI 工具管理财务数据。

### 工作原理

1. 所有命令通过 `python3 scripts/ledger_cli.py <command> '<json_args>'` 调用
2. 数据存储在 SQLite 数据库中
3. Agent 可以通过 `analyze` 命令学习用户习惯

### 关键流程

```
首次使用：导入CSV → 学习习惯 → 开始记账
日常使用：记账 → 查账 → 统计
```

## 文档索引

详细文档位于 `references/` 目录，按需读取：

| 文档 | 内容 | 何时读取 |
|------|------|----------|
| `references/basic.md` | 基础命令 (add/list/search/filter/summary/stats) | 记账、查账、搜索时 |
| `references/modify.md` | 修改命令 (update/delete/restore) | 修改、删除记录时 |
| `references/budget.md` | 预算命令 (budget_set/budget_check/budget_template_*) | 设置、查看预算时 |
| `references/template.md` | 通用记录模板 (template_*) | 使用模板快速记账时 |
| `references/data.md` | 数据命令 (import/export/schema/analyze) | 导入、导出、分析数据时 |
| `references/field-guide.md` | 字段用途说明、场景示例 | 不确定字段怎么填时 |

> 💡 每个参考文档都有对应的日常操作示例，见 `examples/` 目录下同名 `-examples` 文件。
> 例如：读取 `references/basic.md` 时，同时看 `examples/basic-examples.md` 了解真实场景。

## 核心工作流程

### 流程 1：首次使用

```
用户："导入数据" 
→ 询问CSV路径 
→ 执行 import 
→ 建议"学习"
```

### 流程 2：学习用户习惯

当用户说"学习"、"学习我的习惯"、"分析我的数据"时执行以下流程。

**步骤 1：调用 analyze 命令**

```bash
python3 scripts/ledger_cli.py analyze '{}'
```

**步骤 2：阅读分析结果**

仔细阅读分析报告，重点关注：
- 【账户】列表：这些是用户的付款方式/资金来源
- 【商家】列表：这些是用户消费的平台/店铺
- 【类别→子类别】：这些是用户的消费分类习惯
- 【成员】列表：这些是家庭成员
- 【项目】列表：这些是用户的长期项目
- 【商家→类别关联】：学习商家和类别的对应关系
- 【账户→商家关联】：学习账户和商家的区别

**步骤 3：用 remember 保存关键模式**

根据分析结果，用 `remember` 工具保存以下信息到记忆：

1. **账户模式**：用户的常用账户（如信用卡、微信零钱、招商银行等）
2. **商家模式**：用户的常用商家（如拼多多、京东、美团等）
3. **类别模式**：用户的类别→子类别层级关系
4. **成员模式**：用户家庭成员列表
5. **项目模式**：用户的长期项目列表
6. **字段判断规则**：基于数据总结出的字段区分规律

参考格式：

```markdown
# 用户记账习惯

## 账户（= 付款方式/资金来源）
- 信用卡: 1484笔（常用主力账户）
- 微信零钱: 844笔（日常小额支付）
- 招商银行: 273笔（大额收入/转账）

## 商家（= 消费场所/平台）
- 拼多多: 771笔（最常用网购平台）
- 京东: 236笔（网购，品类较全）
- 美团: 235笔（外卖/团购）

## 类别→子类别
- 食品酒水: 早午晚餐/零食/饮料/水果
- 居家物业: 日常用品/房租水电/维修保养
- 休闲娱乐: 数码3C/运动装备

## 成员
- 本人: 2942笔
- 家庭公用: 609笔
- fish: 229笔

## 字段判断规则
- "京东"是商家，不是账户
- "微信零钱"是账户，不是商家
- "食品酒水"是类别，"零食"是子类别
```

**步骤 4：确认学习完成**

告诉用户：
- 已学习完成
- 已记住用户的账户、商家、类别等习惯
- 以后记账时会自动参考这些习惯

**注意事项**：
1. 只保存用户的实际数据模式，不预设任何值
2. 通过"商家→类别关联"和"账户→商家关联"验证字段判断是否正确
3. 如果用户数据有变化，可以重新运行"学习"更新记忆

### 流程 3：日常记账

```
用户："今天花了30块买零食"
→ 根据 field-guide 正确填写字段 
→ 执行 add
```

## 重要规则

### 去重检查

添加记录时自动检查相似记录（同一天+同类型+同金额+同类别的记录）。

- 发现重复时显示警告，不自动插入
- 使用 `"force": true` 跳过检查
- 建议先用 `list` 或 `search` 查看现有记录

### 输出格式

所有命令返回JSON格式：
```json
{
  "success": true,
  "data": "命令输出内容",
  "error": null
}
```

## 快速参考

### 常用命令

```bash
# 记账
python3 scripts/ledger_cli.py add '{"type":"支出","amount":30,"category":"食品酒水","account":"微信零钱"}'

# 查账
python3 scripts/ledger_cli.py list '{"limit":10}'

# 统计
python3 scripts/ledger_cli.py summary '{"year":2026,"month":6}'

# 分析数据
python3 scripts/ledger_cli.py analyze '{}'
```

### 配置

Skills 通过 `.env` 文件或环境变量 `LEDGER_PATH` 配置服务路径。

```bash
# skills/ledger/.env
LEDGER_PATH=/volume1/docker/ledger
```

路径查找优先级：
1. `skills/ledger/.env` 文件中的 `LEDGER_PATH`
2. 系统环境变量 `LEDGER_PATH`
3. 常见部署路径自动检测
4. 脚本相对路径推导

