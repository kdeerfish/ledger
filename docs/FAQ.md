# Ledger 常见问题解答（FAQ）

---

## 📦 安装相关

### Q1: Docker 安装失败怎么办？

**问题**：执行 `docker run` 后容器立即退出

**解决方案**：
```bash
# 1. 检查端口是否被占用
netstat -ano | findstr :5800

# 2. 查看容器日志
docker logs ledger

# 3. 尝试使用其他端口
docker run -d --name ledger -p 5801:5800 -v $(pwd)/data:/data zouzhenglu/ledger:latest
```

### Q2: Windows 桌面版无法启动？

**问题**：双击 `ledger.exe` 后没有反应

**解决方案**：
1. 检查是否被杀毒软件拦截
2. 右键以管理员身份运行
3. 检查 `data` 目录是否有写入权限
4. 查看 `logs` 目录下的日志文件

### Q3: 源码安装依赖失败？

**问题**：`pip install -e .` 报错

**解决方案**：
```bash
# 1. 升级 pip
python -m pip install --upgrade pip

# 2. 使用国内镜像
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 如果还是失败，尝试
pip install flask flask-cors
pip install -e .
```

---

## 📥 导入相关

### Q4: 导入 CSV 失败怎么办？

**问题**：执行导入命令后报错

**解决方案**：
1. **检查文件编码**：确保 CSV 文件是 UTF-8 编码
   ```bash
   # 转换编码
   iconv -f GBK -t UTF-8 input.csv > output.csv
   ```

2. **检查表头**：第一行必须是表头，包含"交易类型"、"日期"、"金额"、"类别"

3. **检查日期格式**：必须是 `YYYY/MM/DD HH:MM` 格式
   ```
   正确：2026/06/15 14:30
   错误：2026-06-15 14:30
   错误：06/15/2026 14:30
   ```

4. **检查金额格式**：必须是数字，不能有货币符号
   ```
   正确：200
   错误：¥200
   错误：200.00元
   ```

### Q5: 导入后数据重复怎么办？

**问题**：导入后发现有重复记录

**解决方案**：
```bash
# 查看重复记录
python scripts/cli.py list --limit 100

# 删除重复记录（保留最新的一条）
python scripts/cli.py deduplicate
```

### Q6: 如何导入微信/支付宝账单？

**问题**：微信/支付宝导出的格式不支持

**解决方案**：
1. **微信**：我 → 服务 → 钱包 → 账单 → 常见问题 → 下载账单
2. **支付宝**：我的 → 账单 → 右上角"..." → 开具交易流水证明
3. **转换格式**：使用 Excel 打开，调整列名和格式，保存为 CSV

---

## 🤖 AI 学习相关

### Q7: 学习后 AI 还是记不住我的习惯？

**问题**：说"学习记账"后，AI 记账时还是不会自动填写

**解决方案**：
1. **确保数据足够**：至少需要 100 条以上的历史记录
2. **重新学习**：再次说"学习记账"或"重新学习记账"
3. **手动告诉 AI**：
   ```
   我一般用微信零钱买早餐
   我打车都用滴滴
   我网购都用信用卡
   ```

### Q8: AI 记错了类别怎么办？

**问题**：AI 把"早餐"识别成了"午餐"

**解决方案**：
```
把刚才那笔的类别改成早餐
把第42条记录的子类别改成早餐
```

### Q9: AI 记错了账户怎么办？

**问题**：AI 用了错误的账户

**解决方案**：
```
把刚才那笔的账户改成微信零钱
我打车都用微信零钱
```

---

## 📝 记账相关

### Q10: 如何修改已记录的账单？

**问题**：记错了金额或类别

**解决方案**：
```bash
# 修改单个字段
"把刚才那笔改成30块"
"把刚才那笔的类别改成交通"

# 修改多个字段
"把第42条记录改成：金额50，类别餐饮，备注午餐"

# 使用命令行
python scripts/cli.py update 42 --amount 50 --category 餐饮
```

### Q11: 如何删除记录？

**问题**：想删除某条记录

**解决方案**：
```bash
# 删除最近一笔
"删掉刚才那笔"

# 删除指定记录
"删除第42条记录"

# 恢复删除的记录
"恢复刚才删掉的记录"

# 使用命令行
python scripts/cli.py delete 42
python scripts/cli.py restore 42
```

### Q12: 如何查看删除的记录？

**问题**：想看看删除了哪些记录

**解决方案**：
```bash
"看看删除的记录"

# 使用命令行
python scripts/cli.py list --include-deleted
```

---

## 📊 统计相关

### Q13: 如何查看某个类别的详细支出？

**问题**：想看"食品酒水"的具体消费

**解决方案**：
```bash
"看看食品酒水的详细情况"
"看看6月份食品酒水花了多少"

# 使用命令行
python scripts/cli.py filter --category 食品酒水 --month 6
```

### Q14: 如何查看某个商家的消费记录？

**问题**：想看在"拼多多"买了什么

**解决方案**：
```bash
"查查我在拼多多买了什么"
"看看拼多多的消费记录"

# 使用命令行
python scripts/cli.py search --keyword 拼多多 --search-type merchant
```

### Q15: 如何查看某个时间段的收支？

**问题**：想看6月1日到6月15日的支出

**解决方案**：
```bash
"看看6月1号到15号的支出"

# 使用命令行
python scripts/cli.py list --start-date 2026-06-01 --end-date 2026-06-15
```

---

## 💰 预算相关

### Q16: 如何设置预算？

**问题**：想设置本月的预算

**解决方案**：
```bash
"设置本月食品预算2000"
"设置6月交通预算500"

# 使用命令行
python scripts/cli.py budget set --category 食品酒水 --amount 2000 --month 6
```

### Q17: 如何查看预算执行情况？

**问题**：想看看预算还剩多少

**解决方案**：
```bash
"看看这个月的预算还剩多少"
"预算执行情况"

# 使用命令行
python scripts/cli.py budget check --month 6
```

### Q18: 预算超支了怎么办？

**问题**：某个类别超支了

**解决方案**：
1. **调整消费**：减少该类别的支出
2. **调整预算**：增加预算额度
   ```
   把食品预算改成3000
   ```
3. **查看明细**：看看具体哪里超支了
   ```
   看看食品酒水的详细情况
   ```

---

## 📤 导出相关

### Q19: 如何导出数据？

**问题**：想导出账单数据

**解决方案**：
```bash
"导出6月份的记录"
"导出所有数据为JSON格式"

# 使用命令行
python scripts/cli.py export --output june.csv --start-date 2026-06-01 --end-date 2026-06-30
python scripts/cli.py export --output all.json --format json
```

### Q20: 导出的数据在哪里？

**问题**：不知道导出的文件在哪里

**解决方案**：
- **Docker 用户**：在 `./data/` 目录下
- **本地用户**：在项目根目录下
- **查看路径**：
  ```
  导出的文件在哪里？
  ```

---

## 🔧 其他问题

### Q21: 如何备份数据？

**问题**：想备份账单数据

**解决方案**：
```bash
# Docker 用户
cp ./data/ledger.db ./data/ledger_backup_$(date +%Y%m%d).db

# 本地用户
cp ledger.db ledger_backup_$(date +%Y%m%d).db

# 使用命令行
python scripts/cli.py backup
```

### Q22: 如何迁移到新设备？

**问题**：换了新设备，想迁移数据

**解决方案**：
1. **备份数据**：复制 `ledger.db` 文件
2. **安装 Ledger**：在新设备安装
3. **恢复数据**：将 `ledger.db` 放到对应目录
4. **启动服务**：启动 Ledger 即可

### Q23: 数据库损坏怎么办？

**问题**：数据库文件损坏

**解决方案**：
```bash
# 1. 尝试修复
sqlite3 ledger.db "PRAGMA integrity_check;"

# 2. 如果修复失败，使用备份
cp ledger_backup.db ledger.db

# 3. 如果没有备份，尝试导出数据
sqlite3 ledger.db ".dump" > dump.sql
sqlite3 new_ledger.db < dump.sql
```

### Q24: 如何更新 Ledger？

**问题**：想升级到最新版本

**解决方案**：
```bash
# Docker 用户
docker pull zouzhenglu/ledger:latest
docker stop ledger
docker rm ledger
docker run -d --name ledger -p 5800:5800 -v $(pwd)/data:/data zouzhenglu/ledger:latest

# 源码用户
git pull
pip install -e .
```

### Q25: 如何联系支持？

**问题**：遇到无法解决的问题

**解决方案**：
1. **查看文档**：[kdeerfish.github.io/ledger](https://kdeerfish.github.io/ledger)
2. **提交 Issue**：[GitHub Issues](https://github.com/kdeerfish/ledger/issues)
3. **查看日志**：
   ```bash
   # Docker 用户
   docker logs ledger
   
   # 本地用户
   cat logs/ledger.log
   ```

---

## 💡 使用技巧

### 技巧 1：批量记账
```
记三笔账：
1. 早餐15块
2. 午餐25块
3. 晚餐30块
```

### 技巧 2：模板记账
```
创建一个早餐模板：金额15，类别食品酒水，子类别早餐，账户微信零钱
以后记账：用早餐模板记一笔
```

### 技巧 3：快捷记账
```
早餐15
打车20
咖啡12
```

### 技巧 4：查看趋势
```
看看今年每个月的支出趋势
对比一下6月和7月的支出
```

### 技巧 5：设置提醒
```
设置每月1号提醒我记账
设置预算超支提醒
```

---

## 📚 相关资源

- **完整文档**：[kdeerfish.github.io/ledger](https://kdeerfish.github.io/ledger)
- **新手指南**：[GETTING_STARTED.md](GETTING_STARTED.md)
- **快速参考**：[QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **GitHub 仓库**：[kdeerfish/ledger](https://github.com/kdeerfish/ledger)
- **问题反馈**：[GitHub Issues](https://github.com/kdeerfish/ledger/issues)
